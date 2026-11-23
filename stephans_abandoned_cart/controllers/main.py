# -*- coding: utf-8 -*-
import logging
from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)


class AbandonedCartRecoveryController(http.Controller):

    @http.route("/shop/cart/recovery/<string:token>", type="http", auth="public", website=True, sitemap=False)
    def recover_abandoned_cart(self, token, **kwargs):
        """Restore customer's abandoned cart into active web session."""
        if not token:
            return request.redirect("/shop")

        order_sudo = request.env["sale.order"].sudo().search([
            ("abandoned_cart_token", "=", token),
        ], limit=1)

        if not order_sudo:
            _logger.warning("Abandoned cart recovery attempted with invalid token: %s", token)
            return request.redirect("/shop")

        if order_sudo.state not in ("draft", "sent"):
            # Already confirmed or cancelled
            _logger.info("Abandoned cart recovery order %s is already in state: %s", order_sudo.name, order_sudo.state)
            return request.redirect("/shop/cart")

        # Set session cart
        request.session["sale_order_id"] = order_sudo.id
        request.session["sale_last_order_id"] = order_sudo.id

        # Update log notes if active log exists
        active_log = request.env["abandoned.cart.log"].sudo().search([
            ("order_id", "=", order_sudo.id),
            ("state", "!=", "recovered"),
        ], limit=1)
        if active_log:
            active_log.write({
                "notes": (active_log.notes or "") + f"\nCart restored via recovery link at {http.request.env['ir.fields.converter'].format_datetime(http.request.env, http.request.env['fields.Datetime'].now()) if hasattr(http.request.env, 'ir.fields.converter') else 'now'}"
            })

        _logger.info("Successfully restored abandoned cart session for order %s (Token: %s)", order_sudo.name, token)
        return request.redirect("/shop/cart")
