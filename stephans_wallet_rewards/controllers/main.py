# -*- coding: utf-8 -*-
import logging

from odoo.http import Controller, request, route

_logger = logging.getLogger(__name__)


class SkyWalletController(Controller):
    _process_url = "/payment/sky_wallet/process"

    @route(_process_url, type="http", auth="user", methods=["POST"], website=True)
    def sky_wallet_process_transaction(self, reference=None, **_kwargs):
        """The customer confirmed paying with Sky Wallet (generic redirect form, CSRF-protected).

        Only the customer who owns the transaction can trigger the debit; the debit itself runs in
        `_apply_updates` (payment processing cron) with a row lock on the wallet.
        """
        tx_sudo = request.env["payment.transaction"].sudo()._search_by_reference(
            "sky_wallet", {"reference": reference}
        )
        own_partner = request.env.user.partner_id.commercial_partner_id
        if tx_sudo and tx_sudo.partner_id.commercial_partner_id == own_partner and tx_sudo.state in ("draft", "pending"):
            tx_sudo._record({"reference": reference, "sky_wallet_authorized": True})
        elif tx_sudo:
            _logger.warning(
                "Sky Wallet: user %s tried to process transaction %s they do not own (state %s).",
                request.env.user.id, reference, tx_sudo.state,
            )
        return request.redirect("/payment/status")
