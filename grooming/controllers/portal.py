# -*- coding: utf-8 -*-
"""
Grooming Portal Controller
Customer portal integration for grooming appointments
"""

from odoo import http
from odoo.http import request
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class GroomingPortal(CustomerPortal):
    """Extend customer portal with grooming appointments"""

    def _get_grooming_partner_ids(self):
        partner = request.env.user.partner_id
        partner_ids = set([partner.id, partner.commercial_partner_id.id])
        phone = partner.phone or partner.mobile or request.env.user.login
        if phone and hasattr(request.env['res.users'], 'find_matching_partner_ids_by_phone'):
            matched_ids = request.env['res.users'].sudo().find_matching_partner_ids_by_phone(phone)
            partner_ids.update(matched_ids)
        return list(partner_ids)

    def _prepare_home_portal_values(self, counters):
        """Add grooming appointment count to portal home"""
        values = super()._prepare_home_portal_values(counters)
        if 'grooming_appointment_count' in counters:
            partner_ids = self._get_grooming_partner_ids()
            values['grooming_appointment_count'] = request.env['grooming.appointment'].sudo().search_count([
                ('partner_id', 'in', partner_ids)
            ])
        return values

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
