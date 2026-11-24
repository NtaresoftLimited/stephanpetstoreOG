# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PosWallet(models.Model):
    _inherit = "pos.wallet"

    @api.model
    def _sky_wallet_for_partner(self, partner):
        """Active Sky Wallet of a customer (the contact itself or its company), or empty recordset."""
        partner = partner.sudo()
        if not partner:
            return self.sudo().browse()
        partner_ids = list({partner.id, partner.commercial_partner_id.id})
        return self.sudo().search(
            [("partner_id", "in", partner_ids), ("state", "=", "confirm")], order="id desc", limit=1
        )


class PosWalletTransaction(models.Model):
    _inherit = "pos.wallet.transaction"

    sale_order_id = fields.Many2one("sale.order", string="Website Order", readonly=True, index="btree_not_null")
    payment_transaction_id = fields.Many2one(
        "payment.transaction", string="Online Payment", readonly=True, index="btree_not_null"
    )

    def _sky_wallet_channel(self):
        """Human label of where the movement happened, for the customer portal."""
        self.ensure_one()
        if self.sale_order_id or self.payment_transaction_id:
            return "Website"
        if self.pos_order_id:
            return self.pos_order_id.config_id.name or "Store"
        return "Store"
