# -*- coding: utf-8 -*-
import logging

from odoo import models
from odoo.exceptions import UserError, ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)

AUTHORIZED_KEY = "sky_wallet_authorized"


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _get_specific_rendering_values(self, processing_values):
        if self.provider_code != "sky_wallet":
            return super()._get_specific_rendering_values(processing_values)
        from odoo.addons.stephans_wallet_rewards.controllers.main import SkyWalletController

        url_params = {"reference": self.reference}
        if request:
            url_params["csrf_token"] = request.csrf_token()
        return {"api_url": SkyWalletController._process_url, "url_params": url_params}

    def _extract_amount_data(self, payment_data):
        if self.provider_code != "sky_wallet":
            return super()._extract_amount_data(payment_data)
        # The wallet is debited with exactly self.amount below; nothing external to compare with.
        return None

    def _sky_wallet_debit(self):
        """Debit the customer's Sky Wallet once for this transaction; return the ledger line."""
        self.ensure_one()
        WalletTx = self.env["pos.wallet.transaction"].sudo()
        existing = WalletTx.search(
            [("payment_transaction_id", "=", self.id), ("payment_type", "=", "DEBIT")], limit=1
        )
        if existing:
            return existing

        wallet = self.env["pos.wallet"]._sky_wallet_for_partner(self.partner_id)
        if not wallet:
            raise UserError(self.env._("This customer has no active Sky Wallet."))
        if self.currency_id != wallet.currency_id:
            raise UserError(self.env._("Sky Wallet only pays in %s.", wallet.currency_id.name))

        order = self.sale_order_ids[:1] if "sale_order_ids" in self._fields else self.env["sale.order"]
        label = order.name or self.reference
        wallet_tx = wallet.debit_wallet(
            amount=self.amount,
            user_id=self.create_uid.id,
            reason=self.env._("Website payment %s", label),
        )
        wallet_tx.write({
            "name": label,
            "sale_order_id": order.id or False,
            "payment_transaction_id": self.id,
        })
        return wallet_tx

    def _apply_updates(self, payment_data):
        if self.provider_code != "sky_wallet":
            return super()._apply_updates(payment_data)
        if self.state == "done":
            return
        if not payment_data.get(AUTHORIZED_KEY):
            self._set_error(self.env._("Sky Wallet payment was not confirmed by the customer."))
            return
        try:
            with self.env.cr.savepoint():
                wallet_tx = self._sky_wallet_debit()
        except (UserError, ValidationError) as e:
            _logger.info("Sky Wallet payment %s refused: %s", self.reference, e)
            self._set_error(str(e.args[0] if e.args else e))
            return
        self.provider_reference = wallet_tx.wallet_id.name
        self._set_done()
        _logger.info("Sky Wallet payment %s debited (%s %s).", self.reference, self.amount, self.currency_id.name)
