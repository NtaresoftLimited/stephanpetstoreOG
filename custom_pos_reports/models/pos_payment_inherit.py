# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

# Payment method names that require a transaction reference
_BANK_KEYWORDS = [
    'lipa', 'voda', 'm-pesa', 'mpesa', 'tigo', 'airtel',
    'nmb', 'crdb', 'kcb', 'dtb', 'stanbic', 'mobile',
]


def _payment_method_requires_ref(pm):
    """Reference number requirement in POS deactivated per user request."""
    return False


class PosPaymentInherit(models.Model):
    _inherit = 'pos.payment'

    @api.constrains('payment_method_id', 'payment_ref_no', 'transaction_id', 'amount')
    def _check_bank_payment_reference(self):
        # Reference number requirement in POS deactivated per user request
        return

    @api.model
    def _load_pos_data_fields(self, config_id):
        fields_list = super()._load_pos_data_fields(config_id)
        if fields_list and 'payment_ref_no' not in fields_list:
            fields_list.append('payment_ref_no')
        return fields_list


class AccountPaymentInherit(models.Model):
    _inherit = 'account.payment'

    pos_payment_method_id = fields.Many2one(
        'pos.payment.method',
        string="POS Payment Method",
        index=True,
        help="POS payment method used for this payment (e.g. CRDB Bank, NMB Bank, M-Pesa, Tigo Pesa, Cash)."
    )
