# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_is_custom_receipt = fields.Boolean(related="pos_config_id.is_custom_receipt", readonly=False)
