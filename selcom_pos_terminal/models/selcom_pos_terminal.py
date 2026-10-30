import logging
import requests
from werkzeug import urls
from selcom_apigw_client import apigwClient

from odoo import fields, models, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class SelcomPosTerminal(models.Model):
    _name = 'selcom.pos.terminal'
    _description = 'Selcom Pos Terminal'

    name = fields.Char()
    apikey = fields.Char(string="Api Key", required=True)
    api_secret = fields.Char(string="Api Secret Key", required=True)
    baseUrl = fields.Char(string="Base Url", required=True)
    payment_method = fields.Char(string="Method")
    msisdn = fields.Char(string="msisdn")

    currency_id = fields.Many2one('res.currency', string='Currency')
    company_id = fields.Many2one('res.company', required=True, default=lambda self: self.env.company)

    def _api_make_payment_request(self, data):
        payment_payload = self._prepare_payment_payload(data)
        _logger.info('PAYLOAD................................%s', payment_payload)
        result = self._selcom_api_call('/checkout/initiate-pos-payment', data=payment_payload)
        _logger.info('result................................%s', result)
        self.env['selcom.pos.terminal.payments']._create_selcom_payment_request(result, {**data,
                                                                                         'terminal_id': self.id})
        return result

    def _prepare_payment_payload(self, data):
        return {
            "currency": data['currency'],
            "amount": data['amount'],
            "payment_method": self.payment_method or "",
            "msisdn": self.msisdn or "",
            "invoice_no": data['order_id'],
        }

    def _selcom_api_call(self, endpoint, data=None):
        for rec in self:
            client = apigwClient.Client(rec.baseUrl, rec.apikey, rec.api_secret)
            promptPaymentPath = f'/v1/{endpoint.strip("/")}'
            response = client.postFunc(promptPaymentPath, data)
            return response

    def show_form_and_tree(self):
        action = self.env['ir.actions.actions']._for_xml_id(
            'selcom_pos_terminal.selcom_pos_terminal_payments_action')
        action.update({
            'domain': [('terminal_id', '=', self.id)],
            'views': [
                (self.env.ref('selcom_pos_terminal.selcom_pos_terminal_payments_view_tree').id,
                 'list'),
                (self.env.ref('selcom_pos_terminal.selcom_pos_terminal_payments_view_form').id,
                 'form')],
            'res_id': self.id,
        })
        return action







