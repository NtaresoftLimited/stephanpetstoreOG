# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_max_percentage_discount = fields.Float(related="pos_config_id.max_percentage_discount", readonly=False)
    pos_max_fixed_amount_discount = fields.Float(related="pos_config_id.max_fixed_amount_discount", readonly=False)
