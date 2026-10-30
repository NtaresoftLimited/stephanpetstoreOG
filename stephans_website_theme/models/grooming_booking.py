from odoo import fields, models

class StephansGroomingBooking(models.Model):
    _name = 'stephans.grooming.booking'
    _description = 'Website Grooming Booking'
    _order = 'create_date desc'

    name = fields.Char(default=lambda self: 'GRM-%s' % fields.Datetime.now().strftime('%Y%m%d%H%M%S'), readonly=True)
    customer_name = fields.Char(required=True)
    customer_phone = fields.Char(required=True)
    customer_email = fields.Char()
    pet_name = fields.Char(required=True)
    pet_type = fields.Selection([
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('small_animal', 'Small Animal')
    ], required=True)
    pet_category = fields.Char(string='Breed Size / Category', required=True)
    service_key = fields.Selection([
        ('standard', 'Essential Package'),
        ('premium', 'Premium Package'),
        ('super_premium', 'Signature Package')
    ], required=True)
    preferred_date = fields.Date(required=True)
    preferred_time = fields.Char(required=True)
    detangling = fields.Boolean()
    notes = fields.Text()
    state = fields.Selection([
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='pending')
