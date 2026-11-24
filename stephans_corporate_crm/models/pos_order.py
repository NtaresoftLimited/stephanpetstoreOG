# -*- coding: utf-8 -*-
from odoo import models, api

class PosOrder(models.Model):
    _inherit = 'pos.order'

    def action_pos_order_paid(self):
        res = super(PosOrder, self).action_pos_order_paid()
        for order in self:
            if order.partner_id:
                currency_symbol = order.currency_id.symbol or 'TZS'
                order.partner_id.recalculate_crm_box(
                    trigger='pos',
                    reason=f"POS Order {order.pos_reference or order.name} paid (Amount: {order.amount_total:,.0f} {currency_symbol})."
                )
        return res

    @api.model
    def _process_order(self, order, draft, existing_order):
        order_id = super(PosOrder, self)._process_order(order, draft, existing_order)
        if order_id:
            pos_rec = self.browse(order_id)
            if pos_rec.partner_id:
                currency_symbol = pos_rec.currency_id.symbol or 'TZS'
                pos_rec.partner_id.recalculate_crm_box(
                    trigger='pos',
                    reason=f"POS transaction completed (Amount: {pos_rec.amount_total:,.0f} {currency_symbol})."
                )
        return order_id
