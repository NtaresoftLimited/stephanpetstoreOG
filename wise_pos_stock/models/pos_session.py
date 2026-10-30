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
        stock_quantities = self.env['stock.quant'].sudo().read_group(
            [('product_id', 'in', product_ids), ('location_id', '=', location)],
            ['product_id', 'quantity'],
            ['product_id']
        )


        # Format result as a dictionary with product_id as key and quantity as value
        for quant in stock_quantities:
            quantities[quant['product_id'][0]] = quant['quantity']

        # Return quantity 0 for products with no stock_quant records
        for product_id in product_ids:
            if product_id not in quantities:
                quantities[product_id] = 0.0

        return quantities

    # def _load_pos_data(self, data):
    #     # Add custom context
    #     context = dict(self.env.context)
    #     # config_id = self.env['pos.config'].browse(data['pos.config']['data'][0]['id'])
    #     # context['location'] = self.config_id.picking_type_id.default_location_src_id.id
    #     #
    #     # # Update session with new context
    #     # self = self.with_context(context)
    #     #
    #     # # Add custom context to params
    #     #
    #     # # Example: Use the modified context in your logic
    #     result = super()._load_pos_data(data)
    #     print(result,"////////////////123result\n\n\n")
    #     # result['context'].update({'location': data['pos.config']['data'][0]['picking_type_location_id']})
    #     result['context']  = {'location': data['pos.config']['data'][0]['picking_type_location_id']}
    #     print(result, "...............result", context)
    #     return result




# class PosSession(models.Model):
#     _inherit = 'pos.session'


