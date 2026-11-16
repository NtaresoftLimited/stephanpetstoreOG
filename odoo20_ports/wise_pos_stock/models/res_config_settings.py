# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_is_display_stock = fields.Boolean(related="pos_config_id.is_display_stock", readonly=False)
    pos_stock_type = fields.Selection(related="pos_config_id.stock_type", readonly=False)
    pos_is_restrict_out_of_stock_products = fields.Boolean(
        related="pos_config_id.is_restrict_out_of_stock_products", readonly=False)
    pos_only_in_stock_products = fields.Boolean(related="pos_config_id.only_in_stock_products", readonly=False)
    pos_is_low_stock_screen_visible = fields.Boolean(
        related="pos_config_id.is_low_stock_screen_visible", readonly=False)
    pos_low_stock_threshold = fields.Integer(related="pos_config_id.low_stock_threshold", readonly=False)
    pos_low_stock_color = fields.Integer(related="pos_config_id.low_stock_color", readonly=False)
    pos_in_stock_color = fields.Integer(related="pos_config_id.in_stock_color", readonly=False)
    pos_stock_quantities_refresh_rate = fields.Selection(
        related="pos_config_id.stock_quantities_refresh_rate", readonly=False)
    pos_stock_warehouse = fields.Selection(related="pos_config_id.stock_warehouse", readonly=False)
    pos_is_restrict_low_margin_products = fields.Boolean(
        related="pos_config_id.is_restrict_low_margin_products", readonly=False)
    pos_margin_threshold_percent = fields.Float(related="pos_config_id.margin_threshold_percent", readonly=False)
    pos_margin_restriction_level = fields.Selection(
        related="pos_config_id.margin_restriction_level", readonly=False)
    pos_margin_check_product_type = fields.Selection(
        related="pos_config_id.margin_check_product_type", readonly=False)
