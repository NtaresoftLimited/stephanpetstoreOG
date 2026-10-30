# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import UserError



class StockPicking(models.Model):
    _inherit = 'stock.picking'
    _description = 'Validate Button Check Done quantity is greater than demand quantity '


    def button_validate(self):
        if not self.picking_type_id.exceeded_quantity:
            for record in self.move_ids_without_package:
                available_qty = self.env['stock.quant'].search([('product_id', '=', self.product_id.id), ('location_id', '=', self.location_id.id)]).inventory_quantity_auto_apply
                if record.quantity > available_qty:
                    raise UserError(' Done quantity is greater than available quantity')
                elif record.quantity > record.product_uom_qty:
                    raise UserError(' Done quantity is greater than demand quantity')
            return super(StockPicking, self).button_validate()
        else:
            return super(StockPicking, self).button_validate()

