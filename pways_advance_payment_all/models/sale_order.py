from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    payment_history_ids = fields.One2many('advance.payment.history','order_id', string="Advanvce Payment Information")
    advance_amount = fields.Float(string="Advance Amount",compute="compute_the_advance_amount")
    so_payment_count = fields.Integer(compute="so_count")

    def compute_the_advance_amount(self):
        for i in self:
            i.advance_amount = sum(i.payment_history_ids.mapped("advance_amount"))

    def set_sale_advance_payment(self):
        view_id = self.env.ref('pways_advance_payment_all.sale_advance_payment_wizard')
        if view_id:
            pay_wiz_data={
                'name' : _('Advance Payment'),
                'type' : 'ir.actions.act_window',
                'view_type' : 'form',
                'view_mode' : 'form',
                'res_model' : 'sale.advance.payment',
                'view_id' : view_id.id,
                'target' : 'new',
                'context' : {
                                'name':self.name,
                                'order_id':self.id,
                                'total_amount':self.amount_total,
                                'company_id':self.company_id.id,
                                'currency_id':self.currency_id.id,
                                'date_order':self.date_order,
                                'currency_rate':self.currency_rate,
                                'partner_id':self.partner_id.id,
                            },
            }
        return pay_wiz_data

    def so_paid(self):
        invoices = self.invoice_ids.mapped('name') + [self.name]
        return {
            'name': 'Sale Payments',
            'domain': [('memo', 'in', invoices)],
            # 'domain': [('name', 'in', invoices)],
            'res_model': 'account.payment',
            'view_id': False,
            'view_mode': 'list,form',
            'type': 'ir.actions.act_window',
        }

    def so_count(self):
        invoices = self.invoice_ids.mapped('name') + [self.name]
        payments = self.env['account.payment'].search([('memo', 'in', invoices)])
        # payments = self.env['account.payment'].search([('name', 'in', invoices)])
        self.so_payment_count = len(payments)
