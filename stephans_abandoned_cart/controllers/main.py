# -*- coding: utf-8 -*-
from datetime import datetime
import hashlib
import logging
from odoo import http, fields, _
from odoo.http import request

_logger = logging.getLogger(__name__)


class AbandonedCartRecoveryController(http.Controller):

    @http.route("/shop/cart/recovery/<string:token>", type="http", auth="public", website=True, sitemap=False)
    def recover_abandoned_cart(self, token, **kwargs):
        """Restore customer's abandoned cart items into active session with zero PII exposure."""
        if not token or len(token) < 16:
            _logger.warning("Abandoned cart recovery attempted with empty or invalid token format.")
            return request.redirect("/shop")

        # Compute SHA-256 hash of incoming token
        token_hash = hashlib.sha256(token.strip().encode("utf-8")).hexdigest()

        order_sudo = request.env["sale.order"].sudo().search([
            ("abandoned_cart_token_hash", "=", token_hash),
        ], limit=1)

        if not order_sudo:
            _logger.warning("Abandoned cart recovery attempted with non-matching token hash.")
            return request.redirect("/shop")

        now = fields.Datetime.now()
        # Verify 48-hour expiration
        if order_sudo.abandoned_cart_token_expiry and order_sudo.abandoned_cart_token_expiry < now:
            _logger.info("Abandoned cart recovery token for order %s has expired (Expiry: %s)", order_sudo.name, order_sudo.abandoned_cart_token_expiry)
            return request.redirect("/shop")

        # Verify order state (must be draft/sent quotation)
        if order_sudo.state not in ("draft", "sent"):
            _logger.info("Abandoned cart recovery order %s is already processed or cancelled (State: %s)", order_sudo.name, order_sudo.state)
            return request.redirect("/shop/cart")

        # 1. Real-time Inventory & Price Revalidation
        adjustment_notes = order_sudo._revalidate_cart_stock_and_prices()

        # 2. Session Isolation & Zero PII Protection
        # Contents-only restoration: Never log user in or prefill address to unauthenticated sessions
        current_user = request.env.user
        public_partner = request.website.user_id.partner_id

        if current_user._is_public():
            # If the restored order is attached to an unauthenticated session, decouple partner address
            # to protect PII until the customer completes portal login or checkout address verification.
            if order_sudo.partner_id != public_partner:
                if not order_sudo.abandoned_cart_partner_id:
                    order_sudo.abandoned_cart_partner_id = order_sudo.partner_id.id
                order_sudo.write({
                    "partner_id": public_partner.id,
                    "partner_invoice_id": public_partner.id,
                    "partner_shipping_id": public_partner.id,
                })
        else:
            # Authenticated user session
            order_sudo.write({
                "partner_id": current_user.partner_id.id,
                "partner_invoice_id": current_user.partner_id.id,
                "partner_shipping_id": current_user.partner_id.id,
            })

        # Set session cart
        request.session["sale_order_id"] = order_sudo.id
        request.session["sale_last_order_id"] = order_sudo.id

        # 3. Comprehensive Audit Trail Logging
        active_log = request.env["abandoned.cart.log"].sudo().search([
            ("order_id", "=", order_sudo.id),
            ("state", "!=", "recovered"),
        ], limit=1)

        log_notes = f"\n[{now}] Cart line items restored into web session via recovery token."
        if adjustment_notes:
            log_notes += f" Adjustments: {', '.join(adjustment_notes)}."

        if active_log:
            active_log.write({
                "notes": (active_log.notes or "") + log_notes,
            })

        _logger.info("Successfully restored abandoned cart session for order %s (Hash: %s...)", order_sudo.name, token_hash[:12])
        return request.redirect("/shop/cart")
