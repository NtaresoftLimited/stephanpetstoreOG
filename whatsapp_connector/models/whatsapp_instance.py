import requests
import logging
from odoo import models, fields, api, _
from odoo.exceptions import UserError

from .res_users import get_config_str

_logger = logging.getLogger(__name__)


class WhatsAppInstance(models.Model):
    _name = 'whatsapp.instance'
    _description = 'WhatsApp Instance (UltraMsg / WASender)'

    name = fields.Char(string='Name', required=True, default='Default Instance')
    api_url = fields.Char(string='API URL', required=True, default='https://api.gengeni.bi')
    instance_id = fields.Char(string='Instance ID', required=True)
    token = fields.Char(string='Token', required=True)
    active = fields.Boolean(default=True)

    # Configuration
    pos_receipt_style = fields.Selection([
        ('standard', 'Standard'),
        ('modern', 'Modern (with Emojis)'),
        ('minimal', 'Minimal (Text Only)'),
    ], string='POS Receipt Style', default='modern', required=True)

    @api.model
    def get_default_instance(self):
        instance = self.search([('active', '=', True)], limit=1)
        return instance

    def _send_via_wasender(self, phone, body, api_key):
        url = "https://wasenderapi.com/api/send-message"
        formatted_phone = phone if str(phone).startswith('+') else f"+{phone}"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {api_key}',
            'User-Agent': 'Odoo/18.0',
        }
        payload = {
            'to': formatted_phone,
            'text': body,
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=12)
            res_json = response.json()
            if response.status_code in (200, 201) and res_json.get('success'):
                return True, res_json
            return False, res_json
        except Exception as e:
            return False, str(e)

    def send_message(self, phone, body):
        self.ensure_one()
        if not phone or not body:
            _logger.warning("WhatsApp: Missing phone or body")
            return False, "Missing phone or body"

        base_url = (self.api_url or '').strip()

        # 1. If instance is configured directly for WASenderAPI
        if "wasenderapi.com" in base_url:
            return self._send_via_wasender(phone, body, self.token)

        # 2. UltraMsg (with white-label support)
        if "gengeni.bi" in base_url:
            base_url = "https://api.ultramsg.com"

        url = f"{base_url}/{self.instance_id}/messages/chat"
        payload = {
            'token': self.token,
            'to': phone,
            'body': body,
        }
        headers = {'content-type': 'application/x-www-form-urlencoded'}

        try:
            _logger.info(f"Sending WhatsApp to {phone} via {self.instance_id}")
            response = requests.post(url, data=payload, headers=headers, timeout=10)
            res_json = response.json()

            if response.status_code == 200 and res_json.get('sent') in ('true', True):
                return True, res_json

            _logger.warning(f"UltraMsg returned non-sent status: {res_json}")
            # Try WASenderAPI fallback if configured in system parameters
            wasender_key = get_config_str(self.env, 'stephans_whatsapp.api_key')
            if wasender_key:
                wa_ok, wa_res = self._send_via_wasender(phone, body, wasender_key)
                if wa_ok:
                    return True, wa_res

            return False, res_json
        except Exception as e:
            _logger.error(f"WhatsApp Exception: {e}")
            return False, str(e)

    def action_test_message(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Send Test Message',
            'res_model': 'whatsapp.test.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_instance_id': self.id},
        }


class WhatsAppTestWizard(models.TransientModel):
    _name = 'whatsapp.test.wizard'
    _description = 'WhatsApp Test Wizard'

    instance_id = fields.Many2one('whatsapp.instance', string='Instance', required=True)
    phone = fields.Char(string='Phone Number', required=True)
    message = fields.Text(string='Message', default='This is a test message from Odoo.')

    def action_send(self):
        self.ensure_one()
        success, response = self.instance_id.send_message(self.phone, self.message)

        if success:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('WhatsApp message sent successfully!'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            raise UserError(_("Failed to send message: %s") % response)
