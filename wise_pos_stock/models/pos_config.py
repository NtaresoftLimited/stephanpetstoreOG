# -*- coding: utf-8 -*-
# Copyright (C) Wisenetic Technologies.

from odoo import fields, models, api


class PosConfig(models.Model):
    _inherit = "pos.config"

    is_display_stock = fields.Boolean(
        default=True, string="Display Stock in POS", help="Enable if you want to show stock of products")
    stock_type = fields.Selection(
        [('on_hand', 'On Hand'), ('forecasted', 'Forecasted')], default='on_hand',  help="Select to show on-hand and forecasted stock on the POS screen", required=True, string="Stock Type")
    is_restrict_out_of_stock_products = fields.Boolean(
        default=True,
        help="Restrict ordering of out-of-stock products based on displayed quantity",
        string="Restrict Product Out of Stock in POS",
    )
    only_in_stock_products = fields.Boolean(
        default=True,
        help="Only display products that have available stock in the current session warehouse/location",
        string="Only In-Stock Products in POS",
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
        [('1', '1 Min.'), ('3', '3 Min.'), ('5', '5 Min.'), ('10', '10 Min.')], default='1',  help="Select the interval to refresh stock quantities on the product screen", required=True, string="Refresh Time")

    stock_warehouse = fields.Selection(
        [('all', 'All Warehouses'), ('current', 'Current Session Warehouse')],
        default='current',  help="Select the warehouse to manage inventory for this point of sale", string="Warehouse Location")

    picking_type_location_id = fields.Many2one(
        related='picking_type_id.default_location_src_id', readonly=False, string="Default Source Location",
        domain="[('usage', '=', 'internal')]")

    in_stock_pick = fields.Integer(
        compute='default_demo', store=True, string='In Stock Pick')

    @api.depends('picking_type_id', 'picking_type_id.default_location_src_id', 'warehouse_id', 'warehouse_id.lot_stock_id')
    def default_demo(self):
        for pos_config in self:
            loc = (
                (pos_config.picking_type_id and pos_config.picking_type_id.default_location_src_id.id)
                or (pos_config.warehouse_id and pos_config.warehouse_id.lot_stock_id.id)
                or 0
            )
            pos_config.in_stock_pick = int(loc)

    @api.model
    def _load_pos_data_fields(self, config_id):
        params = super()._load_pos_data_fields(config_id)
        if params:
            params += [
                'is_display_stock',
                'stock_type',
                'is_restrict_out_of_stock_products',
                'only_in_stock_products',
                'is_low_stock_screen_visible',
                'low_stock_threshold',
                'low_stock_color',
                'in_stock_color',
                'stock_quantities_refresh_rate',
                'stock_warehouse',
                'picking_type_location_id',
                'in_stock_pick',
                'warehouse_id',
                'picking_type_id',
                'is_restrict_low_margin_products',
                'margin_threshold_percent',
                'margin_restriction_level',
                'margin_check_product_type',
            ]
            return list(set(params))
        return []

    @api.depends('session_ids', 'session_ids.state')
    def _compute_last_session(self):
        if self.ids:
            self.env.cr.execute("""
                UPDATE pos_session 
                SET stop_at = write_date 
                WHERE state = 'closed' 
                AND stop_at IS NULL 
                AND config_id IN %s
            """, (tuple(self.ids),))
        return super()._compute_last_session()
