from odoo import fields, models, api
from odoo.tools import BinaryBytes, file_open


class PosPaymentMethod(models.Model):
    _inherit = 'pos.payment.method'

    selcom_pos_terminal_id = fields.Many2one('selcom.pos.terminal', string='Selcom Pos Terminal')
    selcom_latest_response = fields.Json('History', default={})
    selcom_payment_default_partner = fields.Many2one('res.partner')

    def _get_terminal_provider_selection(self):
        return super()._get_terminal_provider_selection() + [('selcom', 'Selcom')]

    def _load_pos_data_fields(self, config):
        return super()._load_pos_data_fields(config) + ['selcom_payment_default_partner']

    def selcom_payment_request(self, data):
        self.sudo().selcom_latest_response = {}  # avoid handling old responses multiple times
        return self.selcom_pos_terminal_id._api_make_payment_request(data)

    @api.model_create_multi
    def create(self, vals_list):
        for val in vals_list:
            if not val.get('custom_image') and val.get('payment_provider') == 'selcom':
                selcom_image = file_open('selcom_pos_terminal/static/src/img/selcom-logo.png', mode='rb').read()
                if selcom_image:
                    val['custom_image'] = BinaryBytes(selcom_image)
        return super().create(vals_list)
