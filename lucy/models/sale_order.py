from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    lucy_order_channel = fields.Selection(
        selection=[
            ("website", "Odoo Website"),
            ("nextjs", "Next.js Website"),
            ("grooming", "Grooming"),
            ("manual", "Manual"),
        ],
        string="LuCy Channel",
        compute="_compute_lucy_order_channel",
        store=True,
        index=True,
    )

    @api.depends("website_id", "origin", "client_order_ref")
    def _compute_lucy_order_channel(self):
        for order in self:
            marker = " ".join(filter(None, (order.origin, order.client_order_ref))).lower()
            if order.website_id:
                order.lucy_order_channel = "website"
            elif "nextjs" in marker or "next.js" in marker:
                order.lucy_order_channel = "nextjs"
            elif "groom" in marker:
                order.lucy_order_channel = "grooming"
            else:
                order.lucy_order_channel = "manual"

