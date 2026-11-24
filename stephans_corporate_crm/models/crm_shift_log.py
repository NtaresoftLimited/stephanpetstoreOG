# -*- coding: utf-8 -*-
from odoo import models, fields, api

class CorporateCrmShiftLog(models.Model):
    _name = 'corporate.crm.shift.log'
    _description = 'Corporate Key Account Box Shift Log'
    _order = 'shift_date desc, id desc'

    name = fields.Char(string='Reference', required=True, copy=False, default='/')
    partner_id = fields.Many2one(
        'res.partner',
        string='Corporate Account',
        required=True,
        ondelete='cascade',
        index=True
    )
    from_box = fields.Selection([
        ('q1', 'Q1: Active (<30 Days)'),
        ('q2', 'Q2: Slipping (1 Month Inactive)'),
        ('q3', 'Q3: Dormant (2-3 Months Inactive)'),
        ('q4', 'Q4: Churned (>3 Months Inactive)'),
    ], string='Previous Box')
    to_box = fields.Selection([
        ('q1', 'Q1: Active (<30 Days)'),
        ('q2', 'Q2: Slipping (1 Month Inactive)'),
        ('q3', 'Q3: Dormant (2-3 Months Inactive)'),
        ('q4', 'Q4: Churned (>3 Months Inactive)'),
    ], string='Current Box', required=True)
    movement_type = fields.Selection([
        ('promoted', 'Promoted 🔺'),
        ('demoted', 'Demoted 🔻'),
        ('initial', 'Initial 📌'),
    ], string='Movement Type', required=True, default='initial')
    shift_date = fields.Datetime(
        string='Shift Date & Time',
        default=fields.Datetime.now,
        required=True,
        index=True
    )
    trigger_source = fields.Selection([
        ('sale', 'Sales Order Confirmation'),
        ('pos', 'POS Order Paid'),
        ('grooming', 'Grooming Appointment Completed'),
        ('cron', 'Nightly Dynamic Shift Cron'),
        ('manual', 'Manual Recalculation'),
    ], string='Trigger Source', default='cron', required=True)
    days_inactive = fields.Integer(string='Days Inactive', default=0)
    total_spend_at_shift = fields.Float(string='Total Spend at Shift (TZS)', default=0.0)
    notes = fields.Text(string='Shift Details / Context')
    user_id = fields.Many2one('res.users', string='Triggered By', default=lambda self: self.env.user)

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals.get('name') == '/':
            seq = self.env['ir.sequence'].next_by_code('corporate.crm.shift.log') or f"SHIFT/{fields.Date.today()}/{self.env['ir.sequence'].next_by_code('base') or '001'}"
            vals['name'] = seq
        return super(CorporateCrmShiftLog, self).create(vals)
