# -*- coding: utf-8 -*-
from odoo import models, fields, api

class GroomingAppointment(models.Model):
    _inherit = 'grooming.appointment'

    corporate_deal_id = fields.Many2one(
        'corporate.crm.deal',
        string='Corporate Deal SLA',
        ondelete='set null',
        index=True
    )

    @api.model_create_multi
    def create(self, vals_list):
        records = super(GroomingAppointment, self).create(vals_list)
        for app in records:
            if app.partner_id:
                app.partner_id.recalculate_crm_box(
                    trigger='grooming',
                    reason=f"Grooming Appointment {app.name} booked for {app.pet_name or 'pet'}."
                )
        return records

    def write(self, vals):
        res = super(GroomingAppointment, self).write(vals)
        if 'state' in vals and vals['state'] in ('checked_in', 'in_progress', 'completed'):
            for app in self:
                if app.partner_id:
                    app.partner_id.recalculate_crm_box(
                        trigger='grooming',
                        reason=f"Grooming Appointment {app.name} marked as {vals['state'].replace('_', ' ').capitalize()} for {app.pet_name or 'pet'}."
                    )
        return res
