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
            # Always return count so the Sky Wallet & Paw Points card is permanently visible on /my
            return "res.partner", [("id", "=", request.env.user.partner_id.id)], "sudo"
        return super()._prepare_portal_counter_values(counter)

    def _sky_wallet_points_cards(self):
        today = fields.Date.context_today(request.env.user)
        return request.env["loyalty.card"].sudo().search([
            ("partner_id", "in", self._sky_wallet_partner_ids()),
            ("program_id.active", "=", True),
            ("program_id.program_type", "=", "loyalty"),
            "|", ("expiration_date", "=", False), ("expiration_date", ">=", today),
        ])

    def _prepare_portal_layout_values(self):
        values = super()._prepare_portal_layout_values()
        partner_ids = self._sky_wallet_partner_ids()
        points_cards = self._sky_wallet_points_cards()
        paw_points = sum(c.points for c in points_cards) if points_cards else 0.0

        wallet = None
        if hasattr(request.env["pos.wallet"], "_sky_wallet_for_partner"):
            wallet = request.env["pos.wallet"]._sky_wallet_for_partner(request.env.user.partner_id)

        pets_count = 0
        if "grooming.pet" in request.env:
            pets_count = request.env["grooming.pet"].sudo().search_count([("partner_id", "in", partner_ids)])

        upcoming_appt = False
        if "grooming.appointment" in request.env:
            upcoming_appt = request.env["grooming.appointment"].sudo().search([
                ("partner_id", "in", partner_ids),
                ("appointment_date", ">=", fields.Datetime.now()),
                ("state", "not in", ("cancelled", "completed")),
            ], order="appointment_date asc", limit=1)

        # 100 points = 5,000 TZS (50 TZS per point)
        paw_points_value = int(paw_points * 50)
        progress_remainder = paw_points % 100
        paw_points_to_next = int(100 - progress_remainder) if progress_remainder > 0 else 100
        paw_points_progress = min(100, int((progress_remainder / 100.0) * 100)) if progress_remainder > 0 else (100 if paw_points > 0 and progress_remainder == 0 else 0)

        values.update({
            "paw_points": paw_points,
            "paw_points_formatted": f"{int(paw_points):,}" if paw_points == int(paw_points) else f"{paw_points:,.1f}",
            "paw_points_value": f"{paw_points_value:,}",
            "paw_points_progress": paw_points_progress,
            "paw_points_to_next": paw_points_to_next,
            "wallet": wallet,
            "wallet_balance_formatted": f"TZS {int(wallet.amount):,}" if wallet and wallet.amount else "TZS 0",
            "wallet_amount_only": f"{int(wallet.amount):,}" if wallet and wallet.amount else "0",
            "pets_count": pets_count,
            "upcoming_appointment": upcoming_appt,
        })
        return values

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
