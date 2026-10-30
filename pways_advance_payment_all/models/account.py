from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class InvoiceMove(models.Model):
    _inherit = 'account.move'

    def action_post(self):
        res = super(InvoiceMove,self).action_post()
        payment_id = self.env['account.payment']
        if not self.env.context.get('check_advance_payment') and self.state == 'posted':
            order_id = self.invoice_line_ids.mapped('sale_line_ids').mapped('order_id')
            if order_id:
                payment_id = self.env['account.payment'].search([('sale_order_id', '=', order_id.id)])
            if not order_id:
                order_id = self.invoice_line_ids.mapped('purchase_line_id.order_id')
                if order_id:
                    payment_id = self.env['account.payment'].search([('purchase_id', '=', order_id.id)])
            if payment_id:
                # payment_move_ids = payment_id.move_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.account_type in ('payable', 'receivable'))
                payment_move_ids = payment_id.move_id.line_ids.filtered(lambda r: not r.reconciled and r.account_id.account_type in ('liability_payable', 'asset_receivable'))
                for payment_move in payment_move_ids:
                    self.js_assign_outstanding_line(payment_move.id)
        return res


class AccountPayment(models.Model):
    _inherit = "account.payment"

    purchase_id = fields.Many2one('purchase.order', string="PO")
    sale_order_id = fields.Many2one('sale.order', copy=False)
    check_advance_payment = fields.Boolean('Check Advance Payment', default=False)

    def _prepare_move_line_default_vals(self, write_off_line_vals=None, force_balance=None):
        ''' Prepare the dictionary to create the default account.move.lines for the current payment.
        :param write_off_line_vals: Optional list of dictionaries to create a write-off account.move.line easily containing:
            * amount:       The amount to be added to the counterpart amount.
            * name:         The label to set on the line.
            * account_id:   The account on which create the write-off.
        :param force_balance: Optional balance.
        :return: A list of python dictionary to be passed to the account.move.line's 'create' method.
        '''
        self.ensure_one()
        write_off_line_vals = write_off_line_vals or {}

        if not self.outstanding_account_id:
            raise UserError(_(
                "You can't create a new payment without an outstanding payments/receipts account set either on the company or the %s payment method in the %s journal.",
                self.payment_method_line_id.name, self.journal_id.display_name))

        # Compute amounts.
        write_off_line_vals_list = write_off_line_vals or []
        write_off_amount_currency = sum(x['amount_currency'] for x in write_off_line_vals_list)
        write_off_balance = sum(x['balance'] for x in write_off_line_vals_list)

        if self.payment_type == 'inbound':
            # Receive money.
            liquidity_amount_currency = self.amount
        elif self.payment_type == 'outbound':
            # Send money.
            liquidity_amount_currency = -self.amount
        else:
            liquidity_amount_currency = 0.0

        if not write_off_line_vals and force_balance is not None:
            sign = 1 if liquidity_amount_currency > 0 else -1
            liquidity_balance = sign * abs(force_balance)
        else:
            liquidity_balance = self.currency_id._convert(
                liquidity_amount_currency,
                self.company_id.currency_id,
                self.company_id,
                self.date,
            )
        counterpart_amount_currency = -liquidity_amount_currency - write_off_amount_currency
        counterpart_balance = -liquidity_balance - write_off_balance
        currency_id = self.currency_id.id

        # Compute a default label to set on the journal items.
        liquidity_line_name = ''.join(x[1] for x in self._get_aml_default_display_name_list())
        counterpart_line_name = ''.join(x[1] for x in self._get_aml_default_display_name_list())

        if self._context.get('check_advance_payment') == True:
            if self.partner_type == 'customer':
                destination_account_id = self.company_id.adv_account_id.id
            else:
                destination_account_id = self.company_id.adv_account_creditors_id.id
        else:
            destination_account_id = self.destination_account_id.id

        line_vals_list = [
            # Liquidity line.
            {
                'name': liquidity_line_name,
                'date_maturity': self.date,
                'amount_currency': liquidity_amount_currency,
                'currency_id': currency_id,
                'debit': liquidity_balance if liquidity_balance > 0.0 else 0.0,
                'credit': -liquidity_balance if liquidity_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.outstanding_account_id.id,
            },
            # Receivable / Payable.
            {
                'name': counterpart_line_name,
                'date_maturity': self.date,
                'amount_currency': counterpart_amount_currency,
                'currency_id': currency_id,
                'debit': counterpart_balance if counterpart_balance > 0.0 else 0.0,
                'credit': -counterpart_balance if counterpart_balance < 0.0 else 0.0,
                'partner_id': self.partner_id.id,
                'account_id': self.destination_account_id.id,
            },
        ]
        return line_vals_list + write_off_line_vals_list
        