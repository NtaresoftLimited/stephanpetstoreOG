from odoo import fields, models


class GroomingAppointment(models.Model):
    _inherit = "grooming.appointment"

    booking_source = fields.Selection(
        selection=[
            ("backend", "Backend"),
            ("odoo_website", "Odoo Website"),
            ("nextjs", "Next.js Website"),
            ("portal", "Customer Portal"),
            ("point_of_sale", "Point of Sale"),
            ("imported", "Imported"),
        ],
        string="Booking Source",
        default="backend",
        required=True,
        index=True,
        tracking=True,
        copy=False,
    )
    website_id = fields.Many2one("website", string="Website", index=True, copy=False)
    website_reference = fields.Char(string="Website Reference", index=True, copy=False)

