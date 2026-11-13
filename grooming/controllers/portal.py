# -*- coding: utf-8 -*-
"""
Grooming Portal Controller
Customer portal integration for grooming appointments and pet profiles
"""

from odoo import fields, http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class GroomingPortal(CustomerPortal):
    """Extend customer portal with grooming appointments and pet profiles"""

    def _get_grooming_partner_ids(self):
        partner = request.env.user.partner_id
        partner_ids = set([partner.id, partner.commercial_partner_id.id])
        phone = getattr(partner, 'phone', False) or getattr(partner, 'mobile', False) or request.env.user.login
        if phone and hasattr(request.env['res.users'], 'find_matching_partner_ids_by_phone'):
            matched_ids = request.env['res.users'].sudo().find_matching_partner_ids_by_phone(phone)
            partner_ids.update(matched_ids)
        return list(partner_ids)

    def _prepare_portal_counter_values(self, counter):
        """Odoo 20 badge counter computation"""
        if counter == 'grooming_appointment_count':
            partner_ids = self._get_grooming_partner_ids()
            return 'grooming.appointment', [('partner_id', 'in', partner_ids)], 'sudo'
        if counter == 'pet_count':
            partner_ids = self._get_grooming_partner_ids()
            return 'grooming.pet', [('partner_id', 'in', partner_ids)], 'sudo'
        if counter == 'pos_order_count':
            partner_ids = self._get_grooming_partner_ids()
            return 'pos.order', [('partner_id', 'in', partner_ids), ('state', 'in', ['paid', 'done', 'invoiced'])], 'sudo'
        return super()._prepare_portal_counter_values(counter)

    def _prepare_home_portal_values(self, counters):
        """Add grooming appointment and pet counts to portal home"""
        values = super()._prepare_home_portal_values(counters)
        partner_ids = self._get_grooming_partner_ids()
        Appointment = request.env['grooming.appointment'].sudo()
        Pet = request.env['grooming.pet'].sudo()

        values['grooming_appointment_count'] = Appointment.search_count([
            ('partner_id', 'in', partner_ids)
        ])
        values['pet_count'] = Pet.search_count([
            ('partner_id', 'in', partner_ids)
        ])
        return values

    # -------------------------------------------------------------------------
    # Grooming Appointments
    # -------------------------------------------------------------------------

    @http.route(['/my/grooming', '/my/grooming/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_grooming_appointments(self, page=1, **kw):
        """List user's grooming appointments"""
        partner_ids = self._get_grooming_partner_ids()
        Appointment = request.env['grooming.appointment'].sudo()

        domain = [('partner_id', 'in', partner_ids)]
        appointment_count = Appointment.search_count(domain)

        pager = portal_pager(
            url='/my/grooming',
            total=appointment_count,
            page=page,
            step=10,
        )

        appointments = Appointment.search(
            domain,
            order='appointment_date desc, id desc',
            limit=10,
            offset=pager['offset']
        )

        return request.render('grooming.portal_my_appointments', {
            'appointments': appointments,
            'page_name': 'grooming_appointments',
            'pager': pager,
            'default_url': '/my/grooming',
        })

    @http.route('/my/grooming/<int:appointment_id>',
                type='http', auth='user', website=True)
    def portal_grooming_appointment_detail(self, appointment_id, **kw):
        """View single grooming appointment details"""
        partner_ids = self._get_grooming_partner_ids()
        appointment = request.env['grooming.appointment'].sudo().search([
            ('id', '=', appointment_id),
            ('partner_id', 'in', partner_ids)
        ], limit=1)

        if not appointment:
            return request.redirect('/my/grooming')

        return request.render('grooming.portal_appointment_detail', {
            'appointment': appointment,
            'page_name': 'grooming_appointment',
        })

    # -------------------------------------------------------------------------
    # My Pets (Pet Management)
    # -------------------------------------------------------------------------

    @http.route(['/my/pets', '/my/pets/page/<int:page>'],
                type='http', auth='user', website=True)
    def portal_my_pets(self, page=1, **kw):
        """List user's registered pets"""
        partner_ids = self._get_grooming_partner_ids()
        Pet = request.env['grooming.pet'].sudo()

        domain = [('partner_id', 'in', partner_ids)]
        pet_count = Pet.search_count(domain)

        pager = portal_pager(
            url='/my/pets',
            total=pet_count,
            page=page,
            step=12,
        )

        pets = Pet.search(
            domain,
            order='name asc, id desc',
            limit=12,
            offset=pager['offset']
        )

        return request.render('grooming.portal_my_pets', {
            'pets': pets,
            'page_name': 'my_pets',
            'pager': pager,
            'default_url': '/my/pets',
        })

    @http.route('/my/pets/<int:pet_id>',
                type='http', auth='user', website=True)
    def portal_my_pet_detail(self, pet_id, **kw):
        """View detailed profile of a registered pet and their grooming history"""
        partner_ids = self._get_grooming_partner_ids()
        pet = request.env['grooming.pet'].sudo().search([
            ('id', '=', pet_id),
            ('partner_id', 'in', partner_ids)
        ], limit=1)

        if not pet:
            return request.redirect('/my/pets')

        appointments = request.env['grooming.appointment'].sudo().search([
            ('pet_id', '=', pet.id)
        ], order='appointment_date desc, id desc', limit=10)

        return request.render('grooming.portal_pet_detail', {
            'pet': pet,
            'appointments': appointments,
            'page_name': 'pet_detail',
        })

    @http.route('/my/pets/new',
                type='http', auth='user', website=True)
    def portal_new_pet_form(self, error=None, **kw):
        """Form to register a new pet"""
        breeds = request.env['grooming.breed'].sudo().search([], order='species asc, name asc')
        return request.render('grooming.portal_pet_new', {
            'breeds': breeds,
            'page_name': 'pet_new',
            'error': error,
        })

    @http.route('/my/pets/create',
                type='http', auth='user', methods=['POST'], website=True)
    def portal_create_pet(self, **post):
        """Handle submission to create a new pet for current customer"""
        Pet = request.env['grooming.pet'].sudo()
        name = (post.get('name') or '').strip()[:80]
        if not name:
            return self.portal_new_pet_form(error="Please enter your pet's name.")

        species_values = dict(Pet._fields['species'].selection)
        species = post.get('species') if post.get('species') in species_values else 'dog'
        gender = post.get('gender') if post.get('gender') in ('male', 'female') else False

        try:
            weight = max(0.0, min(float(post.get('weight') or 0), 150.0))
        except ValueError:
            weight = 0.0

        birth_date = False
        if post.get('birth_date'):
            try:
                birth_date = fields.Date.to_date(post['birth_date'])
            except ValueError:
                birth_date = False
            if birth_date and birth_date > fields.Date.context_today(Pet):
                birth_date = False

        vals = {
            'name': name,
            'species': species,
            'partner_id': request.env.user.partner_id.id,
            'gender': gender,
            'birth_date': birth_date,
            'color': (post.get('color') or '').strip()[:80] or False,
            'weight': weight,
            'notes': (post.get('notes') or '').strip()[:2000] or False,
        }
        breed_id = post.get('breed_id') or ''
        if breed_id.isdigit():
            breed = request.env['grooming.breed'].sudo().browse(int(breed_id)).exists()
            if breed and breed.species == species:
                vals['breed_id'] = breed.id

        Pet.create(vals)
        return request.redirect('/my/pets')
