# -*- coding: utf-8 -*-
from markupsafe import Markup
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class SaleOrderInheritPayment(models.Model):
    _inherit = 'sale.order'

    def action_register_payment(self):
        self.ensure_one()
        amount_due = self.amount_total
        return {
            'name': _('Register Payment: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_order_id': self.id,
                'default_amount': amount_due,
                'default_reference': self.client_order_ref or '',
            },
        }

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped=grouped, final=final, date=date)
        for move in moves:
            if move.state == 'draft':
                try:
                    move.action_post()
                except Exception as e:
                    pass
        return moves


class SaleOrderPaymentWizard(models.TransientModel):
    _name = 'sale.order.payment.wizard'
    _description = 'Register Payment on Proforma / Sale Order'

    order_id = fields.Many2one('sale.order', string='Sale Order', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Customer", related='order_id.partner_id', readonly=True)
    currency_id = fields.Many2one('res.currency', related='order_id.currency_id', string='Currency', readonly=True)
    amount_total = fields.Monetary(string="Order Total", related='order_id.amount_total', readonly=True)
    amount_due = fields.Monetary(string="Amount Due", compute='_compute_amount_due', readonly=True)
    amount = fields.Monetary(string='Payment Amount', required=True, currency_field='currency_id')
    payment_date = fields.Date(string='Payment Date', required=True, default=fields.Date.context_today)

    pos_payment_method_id = fields.Many2one(
        'pos.payment.method',
        string='Payment Method',
        required=True,
        domain="[('active', '=', True), ('journal_id', '!=', False)]",
        help="Select an active payment method (CRDB Bank, NMB Bank, M-Pesa, Tigo Pesa, or Cash)."
    )
    payment_method_type = fields.Selection(related='pos_payment_method_id.type', string='Method Type')
    reference = fields.Char(
        string='Payment Reference / Ref',
        help="Required for CRDB Bank, NMB Bank, M-Pesa, and Tigo Pesa payments (e.g. Transaction ID or Bank Slip)."
    )
    note = fields.Text(string="Internal Note")

    @api.depends('order_id', 'order_id.invoice_ids', 'order_id.amount_total')
    def _compute_amount_due(self):
        for rec in self:
            if not rec.order_id:
                rec.amount_due = 0.0
                continue
            invoices = rec.order_id.invoice_ids.filtered(lambda inv: inv.move_type == 'out_invoice' and inv.state == 'posted')
            if invoices:
                rec.amount_due = sum(invoices.mapped('amount_residual'))
            else:
                rec.amount_due = rec.order_id.amount_total

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        active_id = self.env.context.get('active_id') or self.env.context.get('default_order_id')
        if active_id:
            order = self.env['sale.order'].browse(active_id)
            res['order_id'] = order.id

            posted_invoices = order.invoice_ids.filtered(
                lambda inv: inv.state == 'posted' and inv.move_type == 'out_invoice'
            )
            if posted_invoices:
                residual = sum(posted_invoices.mapped('amount_residual'))
                res['amount'] = residual if residual > 0 else order.amount_total
            else:
                res['amount'] = order.amount_total

            default_pm = self.env['pos.payment.method'].search([
                ('journal_id', '!=', False),
                ('active', '=', True),
                '|', ('company_id', '=', order.company_id.id), ('company_id', '=', False)
            ], limit=1)
            if default_pm:
                res['pos_payment_method_id'] = default_pm.id
        return res

    def action_confirm_payment(self):
        self.ensure_one()
        order = self.order_id

        if self.amount <= 0:
            raise ValidationError(_("Payment amount must be greater than zero."))

        ref_clean = (self.reference or '').strip()
        if self.pos_payment_method_id.type == 'bank' and not ref_clean:
            raise UserError(
                _("A Payment Reference / Ref Number is required for %s. Please enter the transaction ID or bank reference.")
                % self.pos_payment_method_id.name
            )

        journal = self.pos_payment_method_id.journal_id
        if not journal:
            raise UserError(
                _("The selected payment method '%s' does not have an accounting journal configured.")
                % self.pos_payment_method_id.name
            )

        # 1. Confirm Proforma / Quotation if still in draft or sent
        if order.state in ('draft', 'sent'):
            order.action_confirm()

        # 2. Ensure delivery lines can be invoiced immediately
        for line in order.order_line:
            if line.product_id.invoice_policy == 'delivery' and line.qty_delivered < line.product_uom_qty:
                line.qty_delivered = line.product_uom_qty

        # 3. Find or create Customer Invoice
        invoices = order.invoice_ids.filtered(
            lambda inv: inv.move_type == 'out_invoice' and inv.state != 'cancel'
        )
        if not invoices:
            invoices = order._create_invoices()

        if not invoices:
            raise UserError(_("Could not generate an invoice for this order."))

        target_invoice = invoices.filtered(lambda inv: inv.amount_residual > 0)
        if not target_invoice and invoices:
            target_invoice = invoices[0]

        if target_invoice.state == 'draft':
            target_invoice.action_post()

        # 4. Create & Post Payment with Reference Number
        memo_str = f"{order.name} - {ref_clean}" if ref_clean else order.name
        payment_method_line = journal.inbound_payment_method_line_ids[:1]

        payment_vals = {
            'date': self.payment_date,
            'amount': self.amount,
            'payment_type': 'inbound',
            'partner_type': 'customer',
            'memo': memo_str,
            'payment_reference': ref_clean or memo_str,
            'journal_id': journal.id,
            'currency_id': order.currency_id.id,
            'partner_id': order.partner_id.commercial_partner_id.id,
            'pos_payment_method_id': self.pos_payment_method_id.id,
            'company_id': order.company_id.id,
        }
        if payment_method_line:
            payment_vals['payment_method_line_id'] = payment_method_line.id

        payment = self.env['account.payment'].create(payment_vals)
        payment.action_post()

        # 5. Reconcile Payment with Invoice
        domain = [
            ('parent_state', '=', 'posted'),
            ('account_type', 'in', ('asset_receivable', 'liability_payable')),
            ('reconciled', '=', False),
        ]
        payment_lines = payment.move_id.line_ids.filtered_domain(domain)
        invoice_lines = target_invoice.line_ids.filtered_domain(domain)
        if payment_lines and invoice_lines:
            for account in payment_lines.account_id:
                (payment_lines + invoice_lines).filtered(
                    lambda line: line.account_id == account and not line.reconciled
                ).reconcile()

        # 6. Log payment details + reference in Chatter
        formatted_amount = f"{order.currency_id.symbol or 'TSh'} {self.amount:,.2f}"
        body = Markup(
            "<b>Payment Registered:</b> %s via <b>%s</b>"
        ) % (formatted_amount, self.pos_payment_method_id.name)
        if ref_clean:
            body += Markup(" (Ref: <code>%s</code>)") % ref_clean
        if self.note:
            body += Markup("<br/>Note: %s") % self.note

        order.message_post(body=body)
        target_invoice.message_post(body=body)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Payment Registered & Posted'),
                'message': _('Payment of %s confirmed via %s (Ref: %s).') % (
                    formatted_amount,
                    self.pos_payment_method_id.name,
                    ref_clean or 'N/A'
                ),
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }
