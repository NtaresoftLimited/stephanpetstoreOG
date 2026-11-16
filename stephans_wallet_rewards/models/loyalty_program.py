# -*- coding: utf-8 -*-
from odoo import api, models


class LoyaltyProgram(models.Model):
    _inherit = "loyalty.program"

    @api.model
    def _stephans_approve_reward_products(self):
        """Reward discount products are created by Odoo for each loyalty reward. Where the
        product approval workflow (product_auto_code) is installed, unapproved products cannot be
        put on sales orders, which would make every Paw Points redemption fail online."""
        Template = self.env["product.template"]
        if "approval_state" not in Template._fields:
            return
        program = self.env.ref("stephans_wallet_rewards.loyalty_program_paw_points", raise_if_not_found=False)
        if not program:
            return
        templates = program.reward_ids.discount_line_product_id.product_tmpl_id.filtered(
            lambda t: t.approval_state != "approved"
        )
        if templates:
            templates.sudo().write({"approval_state": "approved"})
