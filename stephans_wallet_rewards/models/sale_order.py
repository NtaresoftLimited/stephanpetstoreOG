# -*- coding: utf-8 -*-
"""Online Paw Points: only orders whose customer has an active portal account earn or redeem.

Guest checkouts (customer without a portal user) and the public cart never see loyalty
programs: they are removed from the program domain, so no points are computed, no card is
created and no loyalty reward can be claimed. The checks are repeated at confirmation.
"""
from odoo import models
from odoo.exceptions import UserError
from odoo.fields import Domain

LOYALTY = "loyalty"


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _paw_points_allowed(self):
        self.ensure_one()
        return bool(self.partner_id) and self.partner_id._paw_points_eligible()

    def _get_program_domain(self):
        domain = super()._get_program_domain()
        if not self._paw_points_allowed():
            domain = Domain.AND([domain, [("program_type", "!=", LOYALTY)]])
        return domain

    def _get_trigger_domain(self):
        domain = super()._get_trigger_domain()
        if not self._paw_points_allowed():
            domain = Domain.AND([domain, [("program_id.program_type", "!=", LOYALTY)]])
        return domain

    def _get_claimable_rewards(self, forced_coupons=None):
        res = super()._get_claimable_rewards(forced_coupons=forced_coupons)
        if not self._paw_points_allowed():
            for coupon in [c for c in res if c.program_id.program_type == LOYALTY]:
                del res[coupon]
        return res

    def _apply_program_reward(self, reward, coupon, **kwargs):
        if reward.program_id.program_type == LOYALTY and not self._paw_points_allowed():
            return {"error": self.env._("Log in to your account to use Paw Points.")}
        return super()._apply_program_reward(reward, coupon, **kwargs)

    def _paw_points_strip(self):
        """Remove any loyalty points/rewards from orders of ineligible customers."""
        for order in self:
            if order._paw_points_allowed():
                continue
            if order.order_line.filtered(lambda l: l.reward_id.program_id.program_type == LOYALTY):
                raise UserError(self.env._(
                    "Order %s uses a Paw Points reward, but the customer has no active online "
                    "account. Remove the reward or link the customer to a portal account first.",
                    order.name,
                ))
            order.coupon_point_ids.filtered(
                lambda p: p.coupon_id.program_id.program_type == LOYALTY
            ).sudo().unlink()

    def action_confirm(self):
        self._paw_points_strip()
        return super().action_confirm()

    def _paw_points_estimate(self):
        """Paw Points this cart will earn (for the cart hint)."""
        self.ensure_one()
        return sum(
            self.coupon_point_ids.filtered(
                lambda p: p.coupon_id.program_id.program_type == LOYALTY
            ).mapped("points")
        )

    def _paw_points_program_for_hint(self):
        self.ensure_one()
        return self.env["loyalty.program"].sudo().search([
            ("program_type", "=", LOYALTY), ("active", "=", True), ("ecommerce_ok", "=", True),
            ("website_id", "in", [self.website_id.id, False]),
        ], limit=1)
