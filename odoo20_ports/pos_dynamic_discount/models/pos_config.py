# -*- coding: utf-8 -*-
# Field names, defaults and meaning match the Odoo 18 module so settings copy across unchanged.
from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    max_percentage_discount = fields.Float(
        string="Maximum Percentage Discount",
        default=100.0,
        help="Maximum percentage discount allowed in the POS. Set to 0 for no limit.",
    )
    max_fixed_amount_discount = fields.Float(
        string="Maximum Fixed Amount Discount",
        default=1000000.0,
        help="Maximum fixed amount discount allowed in the POS. Set to 0 for no limit.",
    )
