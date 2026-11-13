# -*- coding: utf-8 -*-
"""In-store Paw Points: only customers with an active portal account earn or redeem.

pos_loyalty recomputes points server-side in `pos.order._process_loyalty`, so this is where the
rule is enforced (the POS screen is patched too, but is not trusted). For an ineligible customer
the sale completes normally with no loyalty points; a loyalty reward on such an order is refused.
"""
from odoo import models
from odoo.exceptions import UserError

LOYALTY = "loyalty"
SKIP_CTX = "paw_points_skip_loyalty"


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _process_loyalty(self):
        self.ensure_one()
        if self.is_refund or (self.partner_id and self.partner_id._paw_points_eligible()):
            # Refunds still reverse what the original order earned/spent.
            return super()._process_loyalty()
        if self.lines.filtered(lambda l: l.is_reward_line and l.reward_id.program_id.program_type == LOYALTY):
            raise UserError(self.env._(
                "Paw Points can only be redeemed by customers with an active online account. "
                "Remove the Paw Points reward from the order and validate again."
            ))
        return super(PosOrder, self.with_context(**{SKIP_CTX: True}))._process_loyalty()


class PosConfig(models.Model):
    _inherit = "pos.config"

    def _get_program_ids(self, check_usage=True):
        programs = super()._get_program_ids(check_usage=check_usage)
        if self.env.context.get(SKIP_CTX):
            programs = programs.filtered(lambda p: p.program_type != LOYALTY)
        return programs
