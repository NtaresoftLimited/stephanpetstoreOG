# -*- coding: utf-8 -*-
"""
Grooming Controllers
Handles web routes for grooming page and booking
"""

from odoo import http
from odoo.http import request
from datetime import datetime, timedelta
import json


class GroomingController(http.Controller):
    """Web controller for grooming pages"""
    
    @http.route('/grooming', type='http', auth='public', website=True)
    def grooming_page(self, **kwargs):
        """Render the grooming booking page"""
        # Fetch Packages
        packages = request.env['grooming.service'].sudo().search([
            ('active', '=', True),
            ('is_addon', '=', False)
        ], order='sequence')
        
        # Fetch Add-ons
        addons = request.env['grooming.service'].sudo().search([
            ('active', '=', True),
            ('is_addon', '=', True)
        ], order='sequence')
        
        # Build Pricing Matrix for JS
        pricing_data = []
        for pkg in packages:
            for line in pkg.price_line_ids:
                pricing_data.append({
                    'package_id': pkg.id,
                    'package_name': pkg.name,
                    'species': line.species,
                    'category': line.size_category,
                    'price': line.price
                })
        
        # Time slots
        time_slots = []
        cursor = datetime.strptime('09:00', '%H:%M')
        end = datetime.strptime('20:00', '%H:%M')
        while cursor <= end:
            time_slots.append((cursor.strftime('%H:%M'), cursor.strftime('%-I:%M %p')))
            cursor += timedelta(minutes=30)
        
        min_date = datetime.now().strftime('%Y-%m-%d')
        
        return request.render('grooming.grooming_page', {
            'packages': packages,
            'addons': addons,
            'pricing_json': json.dumps(pricing_data),
            'time_slots': time_slots,
            'min_date': min_date,
        })
    
    @http.route('/grooming/book', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def book_appointment(self, **post):
        """Handle booking form submission"""
        try:
            # Validate required fields
            required_fields = ['customer_name', 'customer_phone', 'pet_name', 'pet_type', 
                             'pet_category', 'service_id', 'preferred_date', 'preferred_time']
            for field in required_fields:
                if not post.get(field):
                    return request.render('grooming.booking_error', {
                        'error': f'Missing required field: {field.replace("_", " ").title()}'
                    })
            
            # Validate phone number (Tanzanian format)
            phone = post.get('customer_phone', '')
            # Simple soft validation to allow for variations
            if len(phone) < 9: 
                 return request.render('grooming.booking_error', {
                    'error': 'Please enter a valid phone number'
                })
            
            # Find or create partner
            Partner = request.env['res.partner'].sudo()
            partner = Partner.search(['|', ('phone', '=', phone), ('mobile', '=', phone)], limit=1)
            
            if not partner:
                partner = Partner.create({
                    'name': post.get('customer_name'),
                    'phone': phone,
                    'email': post.get('customer_email') or False,
                })
            
            # Parse appointment datetime
            date_str = post.get('preferred_date')
            time_str = post.get('preferred_time')
            
            time_24h = datetime.strptime(time_str, '%H:%M').strftime('%H:%M')
            appointment_dt = datetime.strptime(f'{date_str} {time_24h}', '%Y-%m-%d %H:%M')
            
            # Check for Sunday
            if appointment_dt.weekday() == 6:
                return request.render('grooming.booking_error', {
                    'error': 'We are closed on Sundays. Please choose another day.'
                })
            
            # Get addons
            addon_ids = []
            for key in post:
                if key.startswith('addon_') and post.get(key) == 'on':
                    addon_id = int(key.replace('addon_', '')) # ID passed in name
                    addon_ids.append(addon_id)

            # Extra charges
            has_detangling = post.get('has_detangling') == 'on'
            has_handling = post.get('has_handling') == 'on'
            
            # Create appointment
            Appointment = request.env['grooming.appointment'].sudo()
            appointment = Appointment.create({
                'partner_id': partner.id,
                'pet_name': post.get('pet_name'),
                'pet_type': post.get('pet_type'),
                'pet_category': post.get('pet_category'),
                'service_type': 'full_grooming', # Defaulting to full grooming for package booking
                'service_id': int(post.get('service_id')),
                'addon_ids': [(6, 0, addon_ids)],
                'has_detangling': has_detangling,
                'has_handling': has_handling,
                'appointment_date': appointment_dt,
                'preferred_time': time_str,
                'notes': post.get('notes'),
                'state': 'pending',
            })
            
            return request.render('grooming.booking_success', {
                'appointment': appointment,
            })
            
        except Exception as e:
            return request.render('grooming.booking_error', {
                'error': str(e)
            })
    
    @http.route('/grooming/track', type='http', auth='public', website=True)
    def track_appointment(self, **kwargs):
        """Track appointment status"""
        phone = kwargs.get('phone', '')
        appointments = []
        
        if phone:
            partner = request.env['res.partner'].sudo().search([
                '|', ('phone', '=', phone), ('mobile', '=', phone)
            ], limit=1)
            
            if partner:
                appointments = request.env['grooming.appointment'].sudo().search([
                    ('partner_id', '=', partner.id)
                ], order='appointment_date desc', limit=10)
        
        return request.render('grooming.track_page', {
            'phone': phone,
            'appointments': appointments,
        })
