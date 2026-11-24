# -*- coding: utf-8 -*-
from odoo import models, fields

class CorporateCrmStage(models.Model):
    _name = 'corporate.crm.stage'
    _description = 'Key Account Pipeline Stage'
    _order = 'sequence, id'

    name = fields.Char(string='Stage Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    is_won = fields.Boolean(string='Is Won Stage', default=False, help="Deals in this stage are considered successfully closed & active contracts.")
    is_lost = fields.Boolean(string='Is Lost Stage', default=False, help="Deals in this stage are marked as lost or cancelled.")
    fold = fields.Boolean(string='Folded in Kanban', default=False, help="Fold this stage in Kanban view when empty.")
    requirements = fields.Text(string='Stage Requirements', help="Checklist or criteria required to move opportunities out of this stage.")
