# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    paw_points_eligible = fields.Boolean(
        string="Earns Paw Points",
        compute="_compute_paw_points_eligible",
        help="Loyalty points are only earned and redeemed by customers with an active portal account.",
    )

    def _compute_paw_points_eligible(self):
        eligible_ids = self._paw_points_eligible_ids()
        for partner in self:
            partner.paw_points_eligible = partner.id in eligible_ids

    def _paw_points_eligible_ids(self):
        """Ids among `self` that have an active portal user (res.users active=True, share=True)."""
        ids = [pid for pid in self.ids if pid]
        if not ids:
            return set()
        users = self.env["res.users"].sudo().with_context(active_test=False).search_fetch(
            [("partner_id", "in", ids), ("active", "=", True), ("share", "=", True)], ["partner_id"]
        )
        return set(users.partner_id.ids)

    def _paw_points_eligible(self):
        self.ensure_one()
        return bool(self._paw_points_eligible_ids())

    @api.model
    def _load_pos_data_fields(self, config):
        return super()._load_pos_data_fields(config) + ["paw_points_eligible"]
