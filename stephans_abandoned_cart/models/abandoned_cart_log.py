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
        compute="_compute_partner_id",
        store=True,
        index=True,
    )
    email = fields.Char(
        string="Customer Email",
        compute="_compute_contact_info",
        store=True,
    )
    phone = fields.Char(
        string="Customer Phone",
        compute="_compute_contact_info",
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
            ("email_sent", "Email Sent"),
            ("whatsapp_sent", "WhatsApp Sent"),
            ("multi_sent", "Multi-Channel Sent"),
            ("recovered", "Recovered"),
            ("cancelled", "Cancelled / Expired"),
        ],
        string="Status",
        default="abandoned",
        required=True,
        index=True,
    )
    channel = fields.Selection(
        [
            ("email", "Email"),
            ("whatsapp", "WhatsApp"),
            ("multi", "Multi-Channel"),
        ],
        string="Channel",
        default="email",
        index=True,
    )
    actor = fields.Selection(
        [
            ("cron", "Automated Cron"),
            ("manual", "Staff User"),
        ],
        string="Initiated By",
        default="cron",
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Staff Member",
        index=True,
    )
    delivery_status = fields.Selection(
        [
            ("draft", "Draft / Staged"),
            ("sent", "Sent / Dispatched"),
            ("delivered", "Delivered / Converted"),
            ("failed", "Failed"),
        ],
        string="Delivery Status",
        default="draft",
        index=True,
    )
    abandon_datetime = fields.Datetime(
        string="Abandoned Date",
        default=fields.Datetime.now,
        required=True,
        index=True,
    )
    last_email_sent = fields.Datetime(
        string="Last Email Sent",
        index=True,
    )
    emails_sent_count = fields.Integer(
        string="Emails Sent",
        default=0,
    )
    last_whatsapp_sent = fields.Datetime(
        string="Last WhatsApp Sent",
        index=True,
    )
    whatsapp_sent_count = fields.Integer(
        string="WhatsApp Sent",
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
        string="Audit Trail & History",
    )

    display_name = fields.Char(
        string="Name",
        compute="_compute_display_name",
        store=True,
    )

    @api.depends("order_id.partner_id", "order_id.abandoned_cart_partner_id")
    def _compute_partner_id(self):
        for log in self:
            log.partner_id = log.order_id.abandoned_cart_partner_id or log.order_id.partner_id

    @api.depends("partner_id.email", "partner_id.phone")
    def _compute_contact_info(self):
        for log in self:
            partner = log.partner_id
            log.email = partner.email if partner else False
            log.phone = (getattr(partner, "mobile", False) or partner.phone) if partner else False

    @api.depends("order_id.name", "partner_id.name")
    def _compute_display_name(self):
        for record in self:
            order_name = record.order_id.name or _("New Cart")
            partner_name = record.partner_id.name or _("Guest")
            record.display_name = f"{order_name} - {partner_name}"

    def action_send_reminder(self):
        """Manually trigger sending a branded reminder email for this cart."""
        self.ensure_one()
        if not self.email:
            raise UserError(_("The customer has no email address associated with this order."))
        if self.order_id.state not in ("draft", "sent"):
            raise UserError(_("This order is already confirmed or cancelled."))

        success = self.order_id._send_abandoned_cart_email(log=self, actor="manual", user_id=self.env.uid)
        if success:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Reminder Sent"),
                    "message": _("Branded recovery email sent to %s.", self.email),
                    "type": "success",
                    "sticky": False,
                },
            }
        else:
            raise UserError(_("Failed to send reminder email. Please check your mail settings and template."))

    def action_send_whatsapp(self):
        """Manually trigger sending a WhatsApp reminder message."""
        self.ensure_one()
        if not self.phone:
            raise UserError(_("The customer has no phone number on file for WhatsApp."))
        if self.order_id.state not in ("draft", "sent"):
            raise UserError(_("This order is already confirmed or cancelled."))

        success = self.order_id._send_abandoned_cart_whatsapp(log=self, actor="manual", user_id=self.env.uid)
        if success:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("WhatsApp Reminder Dispatched"),
                    "message": _("Recovery message dispatched to %s.", self.phone),
                    "type": "success",
                    "sticky": False,
                },
            }
        else:
            raise UserError(_("Failed to dispatch WhatsApp reminder."))

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
