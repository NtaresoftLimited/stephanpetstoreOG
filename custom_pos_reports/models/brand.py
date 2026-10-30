from odoo import models, fields

class ProductBrand(models.Model):
    _name = 'product.brand'
    _description = 'Product Brand'
    _order = 'name'

    name = fields.Char(string='Brand Name', required=True)
    logo = fields.Image(string='Logo', max_width=128, max_height=128)
    product_ids = fields.One2many('product.template', 'brand_id', string='Products')
    active = fields.Boolean(default=True)
