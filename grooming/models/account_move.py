# -*- coding: utf-8 -*-
from odoo import models, fields

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    pet_id = fields.Many2one('grooming.pet', string='Pet', help="Pet this invoice is related to")
