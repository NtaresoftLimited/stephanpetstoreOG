# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class AbandonedCartTestWizard(models.TransientModel):
    _name = "abandoned.cart.test.wizard"
    _description = "Send Test Abandoned Cart Reminder Email"

    order_id = fields.Many2one(
        "sale.order",
        string="Sample Cart / Order",
        domain="[('order_line', '!=', False)]",
        help="Select a cart to use its products and total for the preview email.",
    )
    email_to = fields.Char(
        string="Send Test To Email",
        required=True,
        default=lambda self: self.env.user.email or "",
    )
    template_id = fields.Many2one(
        "mail.template",
        string="Email Template",
        domain="[('model', '=', 'sale.order')]",
        required=True,
        default=lambda self: self._default_template_id(),
    )

    @api.model
    def _default_template_id(self):
        ICP = self.env["ir.config_parameter"].sudo()
        template_id = int(ICP.get_param("stephans_abandoned_cart.template_id", 0))
        if template_id and self.env["mail.template"].browse(template_id).exists():
            return template_id
        default_tmpl = self.env.ref("stephans_abandoned_cart.email_template_abandoned_cart", raise_if_not_found=False)
        return default_tmpl.id if default_tmpl else False

    def action_send_test(self):
        self.ensure_one()
        if not self.email_to:
            raise UserError(_("Please provide a destination email address."))

        order = self.order_id
        if not order:
            # Pick latest quotation with order_lines as sample
            order = self.env["sale.order"].search([
                ("order_line", "!=", False),
            ], order="id desc", limit=1)

        if not order:
            raise UserError(_("No sample orders found with cart items. Please create at least one quotation with products first."))

        order._ensure_abandoned_cart_token()

        # Send test mail overriding email_to
        email_values = {
            "email_to": self.email_to,
        }
        self.template_id.sudo().send_mail(
            order.id,
            force_send=True,
            raise_exception=True,
            email_values=email_values,
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Test Email Sent"),
                "message": _("Test abandoned cart reminder email has been dispatched to %s using order %s.", self.email_to, order.name),
                "type": "success",
                "sticky": False,
            },
        }
