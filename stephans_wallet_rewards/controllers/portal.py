# -*- coding: utf-8 -*-
from odoo import fields
from odoo.http import request, route

from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class SkyWalletPortal(CustomerPortal):

    def _sky_wallet_partner_ids(self):
        partner = request.env.user.partner_id
        return list({partner.id, partner.commercial_partner_id.id})

    def _prepare_portal_counter_values(self, counter):
        if counter == "sky_wallet_count":
            # Card shows only for customers who actually have an active Sky Wallet.
            return "pos.wallet", [("partner_id", "in", self._sky_wallet_partner_ids()), ("state", "=", "confirm")], "sudo"
        return super()._prepare_portal_counter_values(counter)

    def _sky_wallet_points_cards(self):
        today = fields.Date.context_today(request.env.user)
        return request.env["loyalty.card"].sudo().search([
            ("partner_id", "in", self._sky_wallet_partner_ids()),
            ("program_id.active", "=", True),
            ("program_id.program_type", "=", "loyalty"),
            "|", ("expiration_date", "=", False), ("expiration_date", ">=", today),
        ])

    @route(["/my/wallet", "/my/wallet/page/<int:page>"], type="http", auth="user", website=True)
    def portal_my_sky_wallet(self, page=1, **_kw):
        wallet = request.env["pos.wallet"]._sky_wallet_for_partner(request.env.user.partner_id)
        WalletTx = request.env["pos.wallet.transaction"].sudo()
        domain = [("wallet_id", "=", wallet.id)] if wallet else [("id", "=", 0)]
        total = WalletTx.search_count(domain)
        pager = portal_pager(url="/my/wallet", total=total, page=page, step=self._items_per_page)
        transactions = WalletTx.search(domain, order="id desc", limit=self._items_per_page, offset=pager["offset"])

        values = self._prepare_portal_layout_values()
        values.update({
            "page_name": "sky_wallet",
            "wallet": wallet,
            "transactions": transactions,
            "pager": pager,
            "points_cards": self._sky_wallet_points_cards(),
            "support_whatsapp": "+255 769 324 445",
        })
        return request.render("stephans_wallet_rewards.portal_my_sky_wallet", values)
