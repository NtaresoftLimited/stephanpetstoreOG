from odoo import models, fields

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    brand_id = fields.Many2one('product.brand', string='Brand')

class GroomingService(models.Model):
    _inherit = 'grooming.service'

    brand_id = fields.Many2one('product.brand', string='Brand')
