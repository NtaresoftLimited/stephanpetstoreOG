# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api
from odoo.exceptions import UserError



class MrpProduction(models.Model):
    _inherit = 'mrp.production'
    _description = 'Validate Button Check Consumed  is greater than To Consume '

    # bom_id = fields.Many2one('mrp.bom',required=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals['bom_id']:
                raise UserError('Please Select Product Bill Of Material')
            rec = super(MrpProduction, self).create(vals)
        return rec

    def button_mark_done(self):
        if not self.bom_id.exceeded_consumed_quantity:
            for record in self.move_raw_ids:
                if record.quantity > record.product_uom_qty:
                    raise UserError(' Consume Quantity Is Greater Than To Consume Quantity')
            return super(MrpProduction, self).button_mark_done()
        else:
            return super(MrpProduction, self).button_mark_done()

