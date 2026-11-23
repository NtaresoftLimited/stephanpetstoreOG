# -*- coding: utf-8 -*-
import hashlib
import hmac
import json
import logging

from odoo import http, _
from odoo.exceptions import AccessDenied, AccessError, UserError
from odoo.http import request

_logger = logging.getLogger(__name__)


class WasenderWebhookController(http.Controller):
    """Authenticated WASender webhook receiver.

    The provider signature authenticates the delivery. Approval commands have a
    second boundary: the originating phone must belong to a configured manager.
    """

    def _raw_body(self):
        return request.httprequest.get_data(cache=True) or b''

    def _verify_signature(self, raw_body):
        secret = request.env['ir.config_parameter'].sudo().get_param(
            'techovers_whatsapp.webhook_secret', '')
        if not secret:
            _logger.error('WASender webhook rejected: no webhook secret configured.')
            return False
        supplied = (
            request.httprequest.headers.get('X-WASender-Signature')
            or request.httprequest.headers.get('X-Webhook-Signature')
            or request.httprequest.headers.get('X-Signature')
            or ''
        ).strip()
        if supplied.lower().startswith('sha256='):
            supplied = supplied.split('=', 1)[1]
        if supplied and hmac.compare_digest(supplied, secret):
            return True
        expected = hmac.new(
            secret.encode('utf-8'), raw_body, hashlib.sha256).hexdigest()
        return bool(supplied and hmac.compare_digest(supplied.lower(), expected.lower()))

    @staticmethod
    def _digits(value):
        return ''.join(character for character in str(value or '') if character.isdigit())

    def _manager_user(self, sender_phone):
        managers = request.env['res.users'].sudo().search([
            ('groups_id', 'in', [
                request.env.ref('techovers_business_suite.group_expense_manager').id,
                request.env.ref('techovers_business_suite.group_techovers_financing_manager').id,
            ]),
            ('active', '=', True),
        ])
        for manager in managers:
            number = manager.partner_id.mobile or manager.partner_id.phone
            if self._digits(number) == sender_phone:
                return manager
        return request.env['res.users']

    def _extract_message(self, payload):
        event = payload.get('event') or payload.get('type') or ''
        data = payload.get('data') or payload.get('payload') or payload
        if not isinstance(data, dict):
            data = {}
        message_data = data.get('messages') or data
        if isinstance(message_data, list):
            message_data = message_data[0] if message_data else {}
        if not isinstance(message_data, dict):
            message_data = {}
        key = message_data.get('key') or {}
        message = (
            message_data.get('messageBody') or message_data.get('body')
            or message_data.get('text') or message_data.get('message') or '')
        if isinstance(message, dict):
            message = message.get('conversation') or message.get('text') or message.get('body') or ''
        sender = (
            key.get('cleanedSenderPn') or key.get('senderPn')
            or message_data.get('from') or message_data.get('sender')
            or message_data.get('phone') or '')
        message_id = (
            key.get('id') or message_data.get('id') or message_data.get('messageId') or payload.get('id')
            or payload.get('messageId') or ''
        )
        return str(event), str(message).strip(), self._digits(sender), str(message_id)

    def _process_approval(self, message, sender_phone):
        parts = message.split(maxsplit=1)
        if len(parts) != 2 or parts[0] not in ('Approve', 'Reject'):
            return False
        reference = parts[1].strip()
        if not reference.startswith(('EXP/', 'FIN/')):
            return False
        actor = self._manager_user(sender_phone)
        if not actor:
            _logger.warning(
                'Rejected WhatsApp approval command from unauthorized number ending %s.',
                sender_phone[-4:])
            return False

        if reference.startswith('EXP/'):
            record = request.env['techovers.expense'].sudo().search(
                [('name', '=', reference)], limit=1)
            if not record:
                return False
            if parts[0] == 'Approve':
                record.with_user(actor).action_approve()
            else:
                record.with_user(actor).action_cancel()
            label = _('Expense')
        else:
            record = request.env['techovers.device.financing'].sudo().search(
                [('name', '=', reference)], limit=1)
            if not record:
                return False
            if parts[0] == 'Approve':
                record.with_user(actor).action_approve()
            else:
                record.with_user(actor).action_reject()
            label = _('Device financing')

        from odoo.addons.techovers_business_suite.models.wasender_api import WasenderHelper
        WasenderHelper.send_message(
            request.env, sender_phone,
            _('%(label)s %(reference)s: %(action)s.',
              label=label, reference=reference, action=parts[0].lower()))
        return True

    def _process_payload(self, payload):
        event, message, sender_phone, message_id = self._extract_message(payload)
        Log = request.env['techovers.whatsapp.log'].sudo() if 'techovers.whatsapp.log' in request.env else None
        if Log and message_id and Log.search_count([('provider_message_id', '=', message_id)]):
            return {'status': 'duplicate'}
        if not sender_phone or not message:
            return {'status': 'ignored'}

        log = None
        if Log:
            log = Log.create({
                'direction': 'incoming',
                'sender_phone': sender_phone,
                'recipient_phone': sender_phone,
                'message_text': message[:4000],
                'event_type': event[:100],
                'provider_message_id': message_id or False,
                'state': 'received',
            })
        try:
            handled = self._process_approval(message, sender_phone)
            if not handled and 'techovers.whatsapp.flow.engine' in request.env:
                # Route to Flow Engine
                engine = request.env['techovers.whatsapp.flow.engine'].sudo()
                handled = engine.process_incoming_message(sender_phone, message)
        except (AccessError, UserError) as error:
            if log:
                log.write({'state': 'failed', 'error_message': str(error)})
            return {'status': 'rejected', 'message': str(error)}
        return {'status': 'processed' if handled else 'logged'}

    @http.route(['/wasender/webhook', '/whatsapp/wasender/webhook'],
                type='json', auth='public', methods=['POST'], csrf=False)
    def wasender_webhook_endpoint(self, **kwargs):
        raw_body = self._raw_body()
        if not self._verify_signature(raw_body):
            raise AccessDenied(_('Invalid webhook signature.'))
        payload = request.dispatcher.jsonrequest or {}
        return self._process_payload(payload)

    @http.route('/wasender/webhook/http', type='http', auth='public',
                methods=['POST', 'GET'], csrf=False)
    def wasender_webhook_http_endpoint(self, **kwargs):
        if request.httprequest.method == 'GET':
            return request.make_response(
                'WASender Webhook Endpoint OK',
                headers=[('Content-Type', 'text/plain')])
        raw_body = self._raw_body()
        if not self._verify_signature(raw_body):
            return request.make_json_response(
                {'status': 'error', 'message': 'Invalid signature'}, status=401)
        try:
            payload = json.loads(raw_body.decode('utf-8')) if raw_body else {}
            return request.make_json_response(self._process_payload(payload))
        except (ValueError, UnicodeDecodeError):
            return request.make_json_response(
                {'status': 'error', 'message': 'Invalid JSON'}, status=400)
