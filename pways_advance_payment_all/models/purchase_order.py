# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    payment_history_ids = fields.One2many('purchase.payment.history','purchase_id')
    advance_payment_history_id = fields.Many2one('purchase.payment.history','purchase_id')
    po_payment_count = fields.Integer(compute="po_count")


    def set_purchase_advance_payment(self):
        view_id = self.env.ref('pways_advance_payment_all.purchase_advance_payment_wizard')
        if view_id:
            pay_wiz_data = {
                'name' : _('Advance Payment'),
                'type' : 'ir.actions.act_window',
                'view_type' : 'form',
                'view_mode' : 'form',
                'res_model' : 'purchase.advance.payment',
                'view_id' : view_id.id,
                'target' : 'new',
                'context' : {
                                'name':self.name,
                                'order_id':self.id,
                                'total_amount':self.amount_total,
                                'company_id':self.company_id.id,
                                'currency_id':self.currency_id.id,
                                'date_order':self.date_order,
                                'partner_id':self.partner_id.id,
                            },
            }
        return pay_wiz_data

    # def po_paid(self):
    #     invoices = self.invoice_ids.mapped('name') + [self.name]
    #     payments = self.env['account.payment'].search([('purchase_id', '=', self.id)])
    #     return {
    #         'name': 'Purchase Payments',
    #         'domain': [('id', 'in', payments.ids)],
    #         'res_model': 'account.payment',
    #         'view_id': False,
    #         'view_mode': 'list,form',
    #         'type': 'ir.actions.act_window',
    #     }

    # def po_count(self):
    #     payments = self.env['account.payment'].search([('purchase_id', '=', self.id)])
    #     self.po_payment_count = len(payments.ids)
        
    def po_paid(self):
        invoices = self.invoice_ids.mapped('name') + [self.name]
        payments = self.env['account.payment'].search([('purchase_id', '=', self.id)])
        return {
            'name': 'Purchase Payments',
            'domain': [('memo', 'in', invoices)],
            'res_model': 'account.payment',
            'view_id': False,
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
        }

    def po_count(self):
        invoices = self.invoice_ids.mapped('name') + [self.name]
        payments = self.env['account.payment'].search([('memo', 'in', invoices)])
        self.po_payment_count = len(payments.ids)
