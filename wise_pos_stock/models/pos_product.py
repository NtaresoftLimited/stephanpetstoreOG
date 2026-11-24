# -*- coding: utf-8 -*-
# Copyright (C) Wisenetic Technologies.

from odoo import models, api, fields

class PosProduct(models.Model):
    _inherit = 'product.product'

    qty_available = fields.Float(string="On Hand Quantity")
    virtual_available = fields.Float(string="Forecasted Quantity")

    @api.model
    def _load_pos_data_fields(self, config_id):
        params = super()._load_pos_data_fields(config_id)
        params += ['qty_available', 'virtual_available', 'standard_price', 'lst_price']
        return list(set(params))

    @api.model
    def wise_get_product_info_pos(self, location, product_ids):
        quantities = {}
        if not product_ids:
            return quantities

        loc_id = None
        if location:
            try:
                loc_id = int(location)
            except (ValueError, TypeError):
                pass

        if loc_id:
            location_domain = [('location_id', 'child_of', loc_id)]
        else:
            location_domain = [('location_id.usage', '=', 'internal')]

        # Ultra-fast grouped query across all product IDs in one single SQL call
        quants = self.env['stock.quant'].sudo().read_group(
            domain=[('product_id', 'in', product_ids)] + location_domain,
            fields=['product_id', 'quantity:sum'],
            groupby=['product_id']
        )
        for q in quants:
            raw_pid = q.get('product_id')
            pid = raw_pid[0] if isinstance(raw_pid, (tuple, list)) else raw_pid
            if pid:
                qty = round(float(q.get('quantity', 0.0) or 0.0), 2)
                quantities[pid] = {
                    'qty_available': qty,
                    'virtual_available': qty,
                }

        # Ensure all requested products return an entry
        for pid in product_ids:
            if pid not in quantities:
                quantities[pid] = {'qty_available': 0.0, 'virtual_available': 0.0}

        return quantities
