# -*- coding: utf-8 -*-
from odoo import models, fields

class PosOrder(models.Model):
    _inherit = 'pos.order'
    
    pet_id = fields.Many2one('grooming.pet', string='Pet', help="Pet this POS order is related to")
