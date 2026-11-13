# -*- coding: utf-8 -*-
from odoo import api, models


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        # Online Sky Wallet payments post to the same cash-type journal the POS wallet method uses.
        res["sky_wallet"] = {"mode": "electronic", "type": ("bank", "cash")}
        return res
