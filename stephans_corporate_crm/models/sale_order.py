# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    corporate_deal_id = fields.Many2one(
        'corporate.crm.deal',
        string='Corporate Opportunity / Deal',
        ondelete='set null',
        index=True
    )

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.partner_id:
                currency_symbol = order.currency_id.symbol or 'TZS'
                order.partner_id.recalculate_crm_box(
                    trigger='sale',
                    reason=f"Sales Order {order.name} confirmed (Amount: {order.amount_total:,.0f} {currency_symbol})."
                )
            if order.corporate_deal_id and not order.corporate_deal_id.is_won:
                order.corporate_deal_id.action_set_won()
        return res
