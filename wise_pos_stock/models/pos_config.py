# -*- coding: utf-8 -*-
# Copyright (C) Wisenetic Technologies.

from email.policy import default
from odoo import fields, models, api


class PosConfig(models.Model):
    _inherit = "pos.config"



    is_display_stock = fields.Boolean(
        default=True, string="Display Stock in POS", help="Enable if you want to show stock of products")
    stock_type = fields.Selection(
        [('on_hand', 'On Hand'), ('forecasted', 'Forecasted')], default='on_hand',  help="Select to show on-hand and forecasted stock on the POS screen", required=True, string="Stock Type")
    is_restrict_out_of_stock_products = fields.Boolean(
        help="Restrict ordering of out-of-stock products based on displayed quantity",
        string="Restrict Product Out of Stock in POS",
    )
    is_low_stock_screen_visible = fields.Boolean(
        default=True, help="Enable to display products with low stock levels on the POS screen",
        string="Low Stock Products Screen",
    )
    low_stock_threshold = fields.Integer(
        default=5,
        help="Select to show on-hand and forecasted stock on the POS screen",
        required=True, readonly=False)

    # Margin Restriction Fields
    is_restrict_low_margin_products = fields.Boolean(
        string="Restrict Low Margin Products",
        help="Block sale of products with margin below threshold",
        default=False,
    )
    margin_threshold_percent = fields.Float(
        string="Minimum Margin (%)",
        help="Minimum profit margin percentage required to sell",
        default=5.0,
    )
    margin_restriction_level = fields.Selection(
        [('block', 'Block Sale'), ('warn', 'Warning Only')],
        string="Restriction Level",
        default='block',
    )
    margin_check_product_type = fields.Selection(
        [('goods', 'Goods Only (Storable/Consumable)'), 
         ('service', 'Services Only'), 
         ('all', 'All Products')],
        string="Apply To",
        default='goods',
        help="Choose which product types to check margins for"
    )

    low_stock_color = fields.Integer(
        default=1, string='Low Stock Color', help='Color displayed for products with low stock levels.', required=True, readonly=False)

    in_stock_color = fields.Integer(
        default=10, string='In Stock Color', help='Color displayed for products with sufficient stock levels.', required=True, readonly=False)

    update_stock_quantities = fields.Selection(
        related="company_id.point_of_sale_update_stock_quantities", readonly=False)

    stock_quantities_refresh_rate = fields.Selection(
        [('1', '1 Min.'), ('3', '3 Min.'), ('5', '5 Min.'), ('10', '10 Min.')], default='3',  help="Select the interval to refresh stock quantities on the product screen", required=True, string="Refresh Time")

    stock_warehouse = fields.Selection(
        [('all', 'All Warehouses'), ('current', 'Current Session Warehouse')],
        default='all',  help="Select the warehouse to manage inventory for this point of sale", string="Warehouse Location")

    picking_type_location_id = fields.Many2one(
        related='picking_type_id.default_location_src_id', readonly=False, string="Default Source Location")

    in_stock_pick = fields.Integer(
        compute='default_demo', string='In Stock Pick')

    @api.depends('picking_type_location_id')
    def default_demo(self):
        for pos_config in self:
            pos_config.in_stock_pick = int(self.picking_type_location_id.id) if self.picking_type_location_id.id else None



    

