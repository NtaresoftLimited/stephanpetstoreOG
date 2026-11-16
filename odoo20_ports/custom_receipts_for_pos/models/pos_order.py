# -*- coding: utf-8 -*-
from odoo import models


class PosOrder(models.Model):
    _inherit = "pos.order"

    def order_receipt_generate_data(self, basic_receipt=False):
        """Server-side receipt data (download / e-mail); the till builds the same in JS."""
        data = super().order_receipt_generate_data(basic_receipt=basic_receipt)
        data["extra_data"]["stephans_change"] = self._order_receipt_format_currency(self.amount_return)
        return data
