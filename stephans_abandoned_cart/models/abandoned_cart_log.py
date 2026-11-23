# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AbandonedCartLog(models.Model):
    _name = "abandoned.cart.log"
    _description = "Abandoned Cart Recovery Log"
    _order = "abandon_datetime desc, id desc"
    _rec_name = "display_name"

    order_id = fields.Many2one(
        "sale.order",
        string="Order / Cart",
        required=True,
        ondelete="cascade",
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="order_id.partner_id",
        store=True,
        index=True,
    )
    email = fields.Char(
        string="Customer Email",
        related="order_id.partner_id.email",
        store=True,
    )
    cart_total = fields.Monetary(
        string="Cart Total",
        related="order_id.amount_total",
        store=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="order_id.currency_id",
    )
    state = fields.Selection(
        [
            ("abandoned", "Abandoned"),
            ("email_sent", "Reminder Sent"),
            ("recovered", "Recovered"),
            ("cancelled", "Cancelled / Expired"),
        ],
        string="Status",
        default="abandoned",
        required=True,
        index=True,
    )
    abandon_datetime = fields.Datetime(
        string="Abandoned Date",
        default=fields.Datetime.now,
        required=True,
        index=True,
    )
    last_email_sent = fields.Datetime(
        string="Last Reminder Sent",
        index=True,
    )
    emails_sent_count = fields.Integer(
        string="Emails Sent",
        default=0,
    )
    recovery_datetime = fields.Datetime(
        string="Recovered Date",
        index=True,
    )
    template_id = fields.Many2one(
        "mail.template",
        string="Template Used",
        domain="[('model', '=', 'sale.order')]",
    )
    notes = fields.Text(
        string="Log Notes",
    )

    display_name = fields.Char(
        string="Name",
        compute="_compute_display_name",
        store=True,
    )

    @api.depends("order_id.name", "partner_id.name")
    def _compute_display_name(self):
        for record in self:
            order_name = record.order_id.name or _("New Cart")
            partner_name = record.partner_id.name or _("Guest")
            record.display_name = f"{order_name} - {partner_name}"

    def action_send_reminder(self):
        """Manually trigger sending a reminder email for this cart."""
        self.ensure_one()
        if not self.email:
            raise UserError(_("The customer has no email address associated with this order."))
        if self.order_id.state not in ("draft", "sent"):
            raise UserError(_("This order is already confirmed or cancelled."))

        success = self.order_id._send_abandoned_cart_email(log=self)
        if success:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Reminder Sent"),
                    "message": _("Abandoned cart reminder email has been sent to %s.", self.email),
                    "type": "success",
                    "sticky": False,
                },
            }
        else:
            raise UserError(_("Failed to send reminder email. Please check your mail settings and template."))

    def action_mark_recovered(self):
        """Mark log as manually recovered."""
        self.write({
            "state": "recovered",
            "recovery_datetime": fields.Datetime.now(),
        })

    def action_view_order(self):
        self.ensure_one()
        return {
            "name": _("Abandoned Cart Order"),
            "type": "ir.actions.act_window",
            "res_model": "sale.order",
            "res_id": self.order_id.id,
            "view_mode": "form",
        }
