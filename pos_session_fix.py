# -*- coding: utf-8 -*-
# Copyright (C) Wisenetic Technologies.

from odoo import models
from odoo import api, fields



class PosProduct(models.Model):
    _inherit = 'product.product'

    qty_available = fields.Float(string="On Hand Quantity")
    virtual_available = fields.Float(string="Forecasted Quantity")

    @api.model
    def _load_pos_data_fields(self, config_id):
        params = super()._load_pos_data_fields(config_id)
        params += ['qty_available', 'virtual_available', 'standard_price', 'lst_price']
        return params

    @api.model
    def wise_get_product_info_pos(self, location, product_ids):
        quantities = {}
        
        # Performance optimization: use read_group for variants
        stock_quantities = self.env['stock.quant'].sudo().read_group(
            [('product_id', 'in', product_ids), ('location_id', '=', location)],
            ['product_id', 'quantity'],
            ['product_id']
        )

        for quant in stock_quantities:
            quantities[quant['product_id'][0]] = quant['quantity']

        # Handling for grouped products or templates if they appear in the POS
        # If a product_id refers to a product that has no direct stock, 
        # check if it's a template record (some modules load them) 
        # or if it has variants that should be summed.
        
        # For each product that returned 0 or wasn't found, check if it's a template
        missing_ids = [pid for pid in product_ids if pid not in quantities or quantities[pid] == 0]
        if missing_ids:
            # Check if these are templates (though this model is product.product)
            # In Odoo, product.product records *are* the variants.
            # If the user sees a tile for a product and it has variants, 
            # we should check if they want the sum.
            products = self.sudo().browse(missing_ids)
            for product in products:
                if product.product_tmpl_id.product_variant_count > 1:
                    # Sum up all variants of this template in this location
                    variant_ids = product.product_tmpl_id.product_variant_ids.ids
                    if variant_ids:
                        v_stocks = self.env['stock.quant'].sudo().read_group(
                            [('product_id', 'in', variant_ids), ('location_id', '=', location)],
                            ['quantity'],
                            []
                        )
                        sum_qty = v_stocks[0]['quantity'] if v_stocks and v_stocks[0]['quantity'] else 0.0
                        quantities[product.id] = sum_qty

        # Final pass to ensure all IDs have an entry
        for product_id in product_ids:
            if product_id not in quantities:
                quantities[product_id] = 0.0

        return quantities
