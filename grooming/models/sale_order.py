# -*- coding: utf-8 -*-
from odoo import models, fields

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    pet_id = fields.Many2one('grooming.pet', string='Pet', help="Pet this order is related to")
    
    def _prepare_invoice(self):
        """Pass pet_id to invoice"""
        invoice_vals = super(SaleOrder, self)._prepare_invoice()
        if self.pet_id:
            invoice_vals['pet_id'] = self.pet_id.id
        return invoice_vals
