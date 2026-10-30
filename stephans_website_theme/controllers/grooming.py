from datetime import datetime, timedelta
import json
from odoo import http
from odoo.http import request

PRICES = {
    'dog': {
        'standard': {'small': 60000, 'medium': 70000, 'large': 80000},
        'super_premium': {'small': 80000, 'medium': 90000, 'large': 100000},
    },
    'cat': {
        'standard': {'kitten': 60000, 'adult': 70000, 'senior': 80000},
        'super_premium': {'kitten': 80000, 'adult': 90000, 'senior': 100000},
    },
    'small_animal': {
        'super_premium': {'hamster': 100000, 'junior_rabbit': 100000, 'adult_rabbit': 150000, 'guinea_pig': 100000},
    },
}

BREED_SIZES = {
    'dog': [
        {'value': 'small', 'label': 'Small Breeds'},
        {'value': 'medium', 'label': 'Medium Breeds'},
        {'value': 'large', 'label': 'Large Breeds'},
    ],
    'cat': [
        {'value': 'kitten', 'label': 'Kitten - (2 - 12 Months)'},
        {'value': 'adult', 'label': 'Adult Cat - (1+ Year)'},
        {'value': 'senior', 'label': 'Senior Cat - (5+ Years)'},
    ],
    'small_animal': [
        {'value': 'hamster', 'label': 'Hamster'},
        {'value': 'junior_rabbit', 'label': 'Junior Rabbit (0 - 6 months)'},
        {'value': 'adult_rabbit', 'label': 'Adult Rabbit (6months +)'},
        {'value': 'guinea_pig', 'label': 'Guinea Pig'},
    ],
}

VALID_TIMES = [
    {'value': '09:00', 'label': '9:00 AM'},
    {'value': '09:30', 'label': '9:30 AM'},
    {'value': '10:00', 'label': '10:00 AM'},
    {'value': '10:30', 'label': '10:30 AM'},
    {'value': '11:00', 'label': '11:00 AM'},
    {'value': '11:30', 'label': '11:30 AM'},
    {'value': '12:00', 'label': '12:00 PM'},
    {'value': '12:30', 'label': '12:30 PM'},
    {'value': '13:00', 'label': '1:00 PM'},
    {'value': '13:30', 'label': '1:30 PM'},
    {'value': '14:00', 'label': '2:00 PM'},
    {'value': '14:30', 'label': '2:30 PM'},
    {'value': '15:00', 'label': '3:00 PM'},
    {'value': '15:30', 'label': '3:30 PM'},
    {'value': '16:00', 'label': '4:00 PM'},
    {'value': '16:30', 'label': '4:30 PM'},
    {'value': '17:00', 'label': '5:00 PM'},
    {'value': '17:30', 'label': '5:30 PM'},
]

class StephansGroomingWebsite(http.Controller):
    @http.route(['/grooming', '/stephans-grooming'], type='http', auth='public', website=True)
    def grooming(self, **kw):
        return request.render('stephans_website_theme.grooming_page', {
            'prices_json': json.dumps(PRICES),
            'breed_sizes_json': json.dumps(BREED_SIZES),
            'valid_times': VALID_TIMES,
            'min_date': datetime.now().strftime('%Y-%m-%d'),
        })

    @http.route('/grooming/book', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def book(self, **post):
        required = ['customer_name', 'customer_phone', 'pet_name', 'pet_type', 'pet_category', 'service_key', 'preferred_date', 'preferred_time']
        if any(not post.get(name) for name in required):
            return request.render('stephans_website_theme.booking_error', {'error': 'Please complete all required fields.'})
        try:
            partner_model = request.env['res.partner'].sudo()
            partner = partner_model.search([
                '|',
                ('phone', '=', post['customer_phone']),
                ('mobile', '=', post['customer_phone']),
            ], limit=1)
            partner_values = {
                'name': post['customer_name'],
                'phone': post['customer_phone'],
                'email': post.get('customer_email') or False,
            }
            if partner:
                partner.write({key: value for key, value in partner_values.items() if value})
            else:
                partner = partner_model.create(partner_values)

            service_xmlids = {
                'standard': 'grooming.grooming_service_standard',
                'premium': 'grooming.grooming_service_premium',
                'super_premium': 'grooming.grooming_service_super',
            }
            service = request.env.ref(service_xmlids[post['service_key']], raise_if_not_found=False)
            appointment_at = datetime.strptime(
                '%s %s' % (post['preferred_date'], post['preferred_time']),
                '%Y-%m-%d %H:%M',
            )
            appointment = request.env['grooming.appointment'].sudo().create({
                'partner_id': partner.id,
                'pet_name': post['pet_name'],
                'pet_type': post['pet_type'],
                'pet_category': post['pet_category'],
                'service_type': 'full_grooming',
                'service_id': service.id if service else False,
                'appointment_date': appointment_at,
                'preferred_time': post['preferred_time'],
                'has_detangling': bool(post.get('has_detangling')),
                'notes': post.get('notes'),
            })
            return request.render('stephans_website_theme.booking_success', {'appointment': appointment})
        except Exception as e:
            return request.render('stephans_website_theme.booking_error', {'error': 'The booking could not be recorded: %s' % str(e)})
