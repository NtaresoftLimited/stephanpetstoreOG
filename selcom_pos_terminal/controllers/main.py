# coding: utf-8
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class PosSelcomController(http.Controller):

    # TODO: '/pos_selcom/webhook' is for backwards compatibility
    # Remove it in v18
    @http.route([
        '/selcom/notification',
    ], type='jsonrpc', methods=['POST'], auth='public', csrf=False)
    def webhook(self, order_type='pos', **post):
        payload = request.httprequest.get_json()
        _logger.info("[POS] Selcom webhook received")
        request.env['selcom.pos.terminal.payments'].sudo()._selcom_process_webhook(payload, order_type)
        return ""
