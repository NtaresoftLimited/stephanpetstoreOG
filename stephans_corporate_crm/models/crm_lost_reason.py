# -*- coding: utf-8 -*-
from odoo import models, fields

class CorporateCrmLostReason(models.Model):
    _name = 'corporate.crm.lost.reason'
    _description = 'Corporate Deal Lost Reason'
    _order = 'sequence, name'

    name = fields.Char(string='Reason', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(default=True)
