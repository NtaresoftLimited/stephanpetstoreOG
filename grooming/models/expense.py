# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import date

class GroomingExpense(models.Model):
    _name = 'grooming.expense'
    _description = 'Grooming Operational Expense'
    _order = 'date desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Description', required=True, tracking=True)
    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    
    category = fields.Selection([
        ('supplies', 'Supplies (Matumizi)'),
        ('utility', 'Utilities (Umeme/Maji)'),
        ('staff', 'Staff/Labor (Posho)'),
        ('transport', 'Transport'),
        ('repair', 'Repairs & Maintenance'),
        ('other', 'Other'),
    ], string='Category', required=True, default='supplies', tracking=True)
    
    amount = fields.Float(string='Amount', required=True, tracking=True)
    
    payment_method_id = fields.Many2one('pos.payment.method', string='Payment Method', required=True, domain="[('company_id', '=', company_id)]")
    
    reference = fields.Char(string='Receipt Ref/Transaction ID')
    receipt_image = fields.Image(string="Receipt", max_width=1024, max_height=1024)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', readonly=True)

    def action_post(self):
        self.write({'state': 'posted'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    def action_draft(self):
        self.write({'state': 'draft'})
