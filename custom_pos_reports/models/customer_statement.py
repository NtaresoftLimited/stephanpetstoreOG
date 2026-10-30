from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from datetime import timedelta


class CustomerStatement(models.TransientModel):
    _name = 'techovers.customer.statement'
    _description = 'TechOvers Customer Statement'

    partner_id = fields.Many2one('res.partner', string='Customer Company/SACCO', required=True)
    date_start = fields.Date(string='Billing Period Start', required=True, default=lambda self: fields.Date.context_today(self).replace(day=1))
    date_end = fields.Date(string='Billing Period End', required=True, default=fields.Date.context_today)

    @api.constrains('partner_id')
    def _check_customer_type(self):
        for record in self:
            name = (record.partner_id.name or '').lower()
            if not record.partner_id.is_company and 'sacco' not in name:
                raise ValidationError(_('Customer Statements are available for company or SACCO customers only.'))

    def _get_statement_data(self):
        self.ensure_one()
        if self.date_end < self.date_start:
            self.date_start, self.date_end = self.date_end, self.date_start
            
        lines = []
        # Pull only posted invoices for the company and its child contacts
        invoices = self.env['account.move'].search([
            ('partner_id', 'child_of', self.partner_id.id),
            ('invoice_date', '>=', self.date_start),
            ('invoice_date', '<=', self.date_end),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
        ], order='invoice_date, id')
        
        for invoice in invoices:
            for line in invoice.invoice_line_ids.filtered(lambda l: not l.display_type):
                lines.append({
                    'customer': invoice.partner_id.name or self.partner_id.name,
                    'date': fields.Date.to_date(invoice.invoice_date).strftime('%d/%m/%Y'),
                    'product': line.name,
                    'qty': line.quantity,
                    'price': line.price_total,
                })
        return {'lines': lines, 'total': sum(line['price'] for line in lines), 'invoices': invoices}

    def action_print_statement(self):
        self.ensure_one()
        return self.env.ref('custom_pos_reports.action_customer_statement').report_action(self)
