# -*- coding: utf-8 -*-
import logging

from odoo import api, fields, models
from odoo.tools import format_amount

from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("sky_wallet", "Sky Wallet")], ondelete={"sky_wallet": "set default"}
    )

    # === BUSINESS METHODS === #

    def _sky_wallet_current_wallet(self, partner=None):
        """Wallet the signed-in customer may spend from, or an empty recordset.

        Only the customer's own wallet is ever usable: a public visitor typing someone's email at
        checkout must never see or spend that person's balance.
        """
        user = self.env.user
        Wallet = self.env["pos.wallet"].sudo()
        if user._is_public():
            return Wallet.browse()
        user_partner = user.partner_id.commercial_partner_id
        if partner and partner.sudo().commercial_partner_id != user_partner:
            return Wallet.browse()
        return Wallet._sky_wallet_for_partner(user.partner_id)

    def _sky_wallet_balance_display(self):
        wallet = self._sky_wallet_current_wallet()
        if not wallet:
            return ""
        return self.env._("Balance: %s", format_amount(self.env, wallet.amount, wallet.currency_id))

    @api.model
    def _find_available_providers(
        self, company_id, partner_id, amount, *args, currency_id=None, report=None, **kwargs
    ):
        providers = super()._find_available_providers(
            company_id, partner_id, amount, *args, currency_id=currency_id, report=report, **kwargs
        )
        wallet_providers = providers.filtered(lambda p: p.code == "sky_wallet")
        if not wallet_providers:
            return providers

        partner = self.env["res.partner"].browse(partner_id).exists()
        wallet = self._sky_wallet_current_wallet(partner)
        currency = self.env["res.currency"].browse(currency_id).exists()
        reason = None
        if not wallet:
            reason = self.env._("The customer has no Sky Wallet, or is not signed in.")
        elif currency and currency != wallet.currency_id:
            reason = self.env._("Sky Wallet only pays in %s.", wallet.currency_id.name)
        elif amount and wallet.currency_id.compare_amounts(wallet.amount, amount) < 0:
            reason = self.env._("Sky Wallet balance is lower than the amount to pay.")
        elif kwargs.get("is_validation"):
            reason = self.env._("Sky Wallet cannot be saved as a payment method.")

        if reason:
            payment_utils.add_to_report(report, wallet_providers, available=False, reason=reason)
            providers -= wallet_providers
        return providers

    def _get_default_payment_method_codes(self):
        self.ensure_one()
        if self.code != "sky_wallet":
            return super()._get_default_payment_method_codes()
        return {"sky_wallet"}

    # === SETUP === #

    @api.model
    def _sky_wallet_link_journal(self):
        """Post online wallet payments to the journal of the POS "Sky Wallet" payment method."""
        for provider in self.search([("code", "=", "sky_wallet")]):
            if provider.journal_id and provider.journal_id.type == "cash":
                continue
            pos_method = self.env["pos.payment.method"].sudo().search(
                [("wallet_method", "=", True), ("company_id", "in", [provider.company_id.id, False])],
                limit=1,
            )
            journal = pos_method.journal_id
            if not journal:
                _logger.warning(
                    "Sky Wallet: no POS wallet payment method/journal found for %s; set the provider "
                    "journal manually.", provider.company_id.name,
                )
                continue
            provider.journal_id = journal
