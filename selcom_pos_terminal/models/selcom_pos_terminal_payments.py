import logging

from odoo import fields, models, api,_
from odoo.exceptions import ValidationError, AccessError, UserError
_logger = logging.getLogger(__name__)


class SelcomPosTerminal(models.Model):
    _name = 'selcom.pos.terminal.payments'
    _description = 'Selcom Pos Terminal'

    name = fields.Char("Transaction ID")
    selcom_uid = fields.Char("Selcom UID")
    reference = fields.Char("Reference")
    order_id = fields.Char('Order')
    terminal_id = fields.Many2one('selcom.pos.terminal')
    session_id = fields.Many2one('pos.session')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency')
    amount = fields.Monetary('Amount', currency_field='currency_id')
    selcom_latest_response = fields.Json('Response', default={})
    status = fields.Selection([
        ('SUCCESS', 'SUCCESS'),
        ('FAILED', 'FAILED'),
        ('PENDING', 'PENDING'),
    ])

    def _create_selcom_payment_request(self, response, data):
        if response and response.get('result') == 'SUCCESS':
            res = self.create({
                'name': response.get('reference'),
                'selcom_uid': data.get('selcom_uid'),
                'terminal_id': data.get('terminal_id'),
                'session_id': data.get('session_id'),
                'order_id': data.get('order_id'),
                'currency_id': data.get('currency_id'),
                'company_id': data.get('company_id'),
                'amount': data.get('amount'),
                'selcom_latest_response': response,
                'status': 'PENDING',
            })

    def update_status(self, order):
        records = self.search([('order_id', '=', order), ('status', '=', 'PENDING')])
        if records:
            for rec in records:
                # Update the status of the found record (you can modify as needed)
                rec.status = 'FAILED'

    @api.model
    def get_selcom_payment_status(self, transaction_id=None, selcom_uid=None):
        domain = []
        if transaction_id:
            domain.append(('name', '=', transaction_id))
        elif selcom_uid:
            domain.append(('selcom_uid', '=', selcom_uid))
        else:
            return {}
        selcom_payment = self.search(domain, limit=1)
        if selcom_payment:
            return selcom_payment.selcom_latest_response
        return {}

    def _selcom_process_webhook(self, webhook_data, order_type='pos'):
        _logger.info('webhook data................................%s',webhook_data)
        selcom_payment = self.sudo().search([('order_id', '=', webhook_data.get('remarks')), ('status', '=', 'PENDING')],limit=1)
        if selcom_payment:
            payment_status = webhook_data.get('result')
            if payment_status:
                selcom_payment.write({
                    'selcom_latest_response': webhook_data,
                    'status': payment_status
                })
            pos_session_sudo = self.env["pos.session"].sudo().browse(selcom_payment.session_id.id)
            pos_session_sudo.config_id._notify("SELCOM_TERMINAL_RESPONSE",
                                               pos_session_sudo.config_id.id)
        else:
            raise ValidationError(_("reference not matched."))

