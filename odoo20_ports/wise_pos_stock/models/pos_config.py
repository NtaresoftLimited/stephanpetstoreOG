# -*- coding: utf-8 -*-
# Field names and values match the Odoo 18 module so settings can be copied across.
from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    is_display_stock = fields.Boolean(
        default=True, string="Display Stock in POS", help="Show the stock of each product on the product cards.")
    stock_type = fields.Selection(
        [("on_hand", "On Hand"), ("forecasted", "Forecasted")], default="on_hand", required=True,
        string="Stock Type", help="Show on-hand or forecasted stock on the POS screen.")
    is_restrict_out_of_stock_products = fields.Boolean(
        default=True, string="Restrict Product Out of Stock in POS",
        help="Block selling more than the stock available at this till's location (services excepted).")
    only_in_stock_products = fields.Boolean(
        default=True, string="Only In-Stock Products in POS",
        help="Hide products that have no stock at this till's location.")
    is_low_stock_screen_visible = fields.Boolean(
        default=True, string="Low Stock Products Screen",
        help="Add a Low Stock list to the POS menu.")
    low_stock_threshold = fields.Integer(default=5, required=True, string="Low Stock Threshold")
    low_stock_color = fields.Integer(default=1, required=True, string="Low Stock Color")
    in_stock_color = fields.Integer(default=10, required=True, string="In Stock Color")
    stock_quantities_refresh_rate = fields.Selection(
        [("1", "1 Min."), ("3", "3 Min."), ("5", "5 Min."), ("10", "10 Min.")], default="1", required=True,
        string="Refresh Time", help="How often the POS reloads stock quantities.")
    stock_warehouse = fields.Selection(
        [("all", "All Warehouses"), ("current", "Current Session Warehouse")], default="current",
        string="Warehouse Location", help="Count stock of this till's location only, or of all warehouses.")
    picking_type_location_id = fields.Many2one(
        related="picking_type_id.default_location_src_id", readonly=False, string="Default Source Location",
        domain="[('usage', '=', 'internal')]")
    in_stock_pick = fields.Integer(compute="_compute_in_stock_pick", store=True, string="In Stock Pick")

    is_restrict_low_margin_products = fields.Boolean(
        default=False, string="Restrict Low Margin Products",
        help="Block sale of products with margin below threshold.")
    margin_threshold_percent = fields.Float(default=5.0, string="Minimum Margin (%)")
    margin_restriction_level = fields.Selection(
        [("block", "Block Sale"), ("warn", "Warning Only")], default="block", string="Restriction Level")
    margin_check_product_type = fields.Selection(
        [("goods", "Goods Only (Storable/Consumable)"), ("service", "Services Only"), ("all", "All Products")],
        default="goods", string="Apply To")

    @api.depends("picking_type_id", "picking_type_id.default_location_src_id",
                 "warehouse_id", "warehouse_id.lot_stock_id")
    def _compute_in_stock_pick(self):
        for config in self:
            location = config.picking_type_id.default_location_src_id or config.warehouse_id.lot_stock_id
            config.in_stock_pick = location.id or 0

    def _wise_stock_location(self):
        """Location whose stock the till shows; empty recordset means all warehouses."""
        self.ensure_one()
        if self.stock_warehouse == "all":
            return self.env["stock.location"]
        return self.picking_type_id.default_location_src_id or self.warehouse_id.lot_stock_id
