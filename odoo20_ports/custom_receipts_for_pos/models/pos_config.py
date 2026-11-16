# -*- coding: utf-8 -*-
from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    # Same field name as the Odoo 18 module, so the till setting copies across unchanged.
    is_custom_receipt = fields.Boolean(
        string="Stephan's Receipt Design",
        help="Print receipts in the Stephan's Pet Store layout (Design 3) instead of the standard one.",
    )
