# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import models, api, fields, _
from odoo.exceptions import UserError


class PosWalletCancellation(models.TransientModel):
    _name = 'pos.wallet.cancellation'
    _description = 'Sky Wallet Cancellation'

    cancel_reason = fields.Text('Cancellation Reason', required=True)

    def cancel_wallet(self):
        self.ensure_one()
        active_id = self.env.context.get('active_id', False)
        if not active_id:
            return
        wallet = self.env['pos.wallet'].browse(active_id)
        if wallet:
            if wallet.amount > 0:
                currency_sym = wallet.currency_id.symbol or wallet.currency_id.name or ''
                raise UserError(
                    _("Cannot cancel wallet '%(wallet)s' with an active balance of %(bal)s %(curr)s.\n\n"
                      "Customer funds cannot be erased through cancellation. "
                      "Please issue a formal refund or write-off via ledger transaction before cancelling.",
                      wallet=wallet.name,
                      bal=wallet.amount,
                      curr=currency_sym)
                )
            wallet.sudo().write({
                'state': 'cancel',
                'reason': self.cancel_reason,
            })
            if wallet.partner_id:
                wallet.partner_id.sudo().write({'wallet_id': False})
