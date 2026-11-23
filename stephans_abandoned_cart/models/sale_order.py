# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import logging
import uuid
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    abandoned_cart_token = fields.Char(
        string="Cart Recovery Token",
        copy=False,
        index=True,
        help="Unique secret token used to restore an abandoned cart session safely.",
    )
    abandoned_cart_state = fields.Selection(
        [
            ("active", "Active Cart"),
            ("abandoned", "Abandoned"),
            ("recovered", "Recovered"),
        ],
        string="Abandoned Cart Status",
        default="active",
        copy=False,
        index=True,
    )
    abandoned_cart_log_ids = fields.One2many(
        "abandoned.cart.log",
        "order_id",
        string="Abandoned Cart Logs",
    )
    abandoned_cart_log_count = fields.Integer(
        string="Abandoned Logs Count",
        compute="_compute_abandoned_cart_log_count",
    )
    cart_recovery_url = fields.Char(
        string="Cart Recovery URL",
        compute="_compute_cart_recovery_url",
    )

    @api.depends("abandoned_cart_log_ids")
    def _compute_abandoned_cart_log_count(self):
        for order in self:
            order.abandoned_cart_log_count = len(order.abandoned_cart_log_ids)

    def _ensure_abandoned_cart_token(self):
        """Ensure order has a unique recovery token generated."""
        for order in self:
            if not order.abandoned_cart_token:
                order.abandoned_cart_token = uuid.uuid4().hex

    def _compute_cart_recovery_url(self):
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "")
        for order in self:
            if not order.abandoned_cart_token:
                order._ensure_abandoned_cart_token()
            order.cart_recovery_url = f"{base_url.rstrip('/')}/shop/cart/recovery/{order.abandoned_cart_token}"

    def action_view_abandoned_cart_logs(self):
        self.ensure_one()
        return {
            "name": _("Abandoned Cart Logs"),
            "type": "ir.actions.act_window",
            "res_model": "abandoned.cart.log",
            "domain": [("order_id", "=", self.id)],
            "view_mode": "tree,form",
            "context": {"default_order_id": self.id},
        }

    def _send_abandoned_cart_email(self, log=None, template=None):
        """Send recovery email to customer and record log."""
        self.ensure_one()
        self._ensure_abandoned_cart_token()

        if not self.partner_id.email:
            _logger.info("Cannot send abandoned cart email for order %s: missing email", self.name)
            return False

        ICP = self.env["ir.config_parameter"].sudo()
        template_id = (
            template.id
            if template
            else int(ICP.get_param("stephans_abandoned_cart.template_id", 0))
        )

        mail_template = None
        if template_id:
            mail_template = self.env["mail.template"].browse(template_id).exists()
        if not mail_template:
            mail_template = self.env.ref(
                "stephans_abandoned_cart.email_template_abandoned_cart",
                raise_if_not_found=False,
            )

        if not mail_template:
            _logger.error("No valid abandoned cart mail template found.")
            return False

        if not log:
            log = self.env["abandoned.cart.log"].search(
                [("order_id", "=", self.id), ("state", "!=", "recovered")],
                limit=1,
            )
            if not log:
                log = self.env["abandoned.cart.log"].create({
                    "order_id": self.id,
                    "abandon_datetime": fields.Datetime.now(),
                    "state": "abandoned",
                    "template_id": mail_template.id,
                })

        try:
            # Send the email using the template
            mail_template.sudo().send_mail(
                self.id,
                force_send=True,
                raise_exception=False,
            )

            now = fields.Datetime.now()
            log.write({
                "state": "email_sent",
                "last_email_sent": now,
                "emails_sent_count": log.emails_sent_count + 1,
                "template_id": mail_template.id,
            })
            self.write({"abandoned_cart_state": "abandoned"})
            _logger.info("Abandoned cart email sent for order %s to %s", self.name, self.partner_id.email)
            return True
        except Exception as e:
            _logger.exception("Failed to send abandoned cart email for order %s: %s", self.name, str(e))
            if log:
                log.write({"notes": f"Error sending email: {str(e)}"})
            return False

    @api.model
    def _cron_check_abandoned_carts(self):
        """Cron job: Identifies abandoned eCommerce carts and sends reminder emails."""
        ICP = self.env["ir.config_parameter"].sudo()
        is_enabled = ICP.get_param("stephans_abandoned_cart.enabled", "True").lower() in ("true", "1")
        if not is_enabled:
            _logger.info("Abandoned cart recovery is disabled in settings. Skipping cron.")
            return

        delay_minutes = int(ICP.get_param("stephans_abandoned_cart.delay_minutes", 30))
        reminder_delay_minutes = int(ICP.get_param("stephans_abandoned_cart.reminder_delay_minutes", 15))
        max_reminders = int(ICP.get_param("stephans_abandoned_cart.max_reminders", 2))

        now = fields.Datetime.now()
        abandon_threshold = now - timedelta(minutes=delay_minutes)

        # Orders in quotation state, associated with website, having lines and customer email
        candidate_orders = self.search([
            ("state", "in", ["draft", "sent"]),
            ("website_id", "!=", False),
            ("order_line", "!=", False),
            ("partner_id.email", "!=", False),
            ("write_date", "<=", abandon_threshold),
            ("abandoned_cart_state", "!=", "recovered"),
        ])

        _logger.info("Found %d candidate abandoned cart orders for review.", len(candidate_orders))

        for order in candidate_orders:
            log = self.env["abandoned.cart.log"].search([
                ("order_id", "=", order.id),
                ("state", "!=", "recovered"),
            ], limit=1)

            if not log:
                # First time detected as abandoned
                log = self.env["abandoned.cart.log"].create({
                    "order_id": order.id,
                    "abandon_datetime": now,
                    "state": "abandoned",
                })
                order.write({"abandoned_cart_state": "abandoned"})

            # Check if we should send a reminder email
            if log.emails_sent_count >= max_reminders:
                continue

            can_send = False
            if log.emails_sent_count == 0:
                # Check if reminder delay has elapsed since cart abandonment
                if log.abandon_datetime and log.abandon_datetime <= (now - timedelta(minutes=reminder_delay_minutes)):
                    can_send = True
            else:
                # Subsequent reminders: wait 24 hours between reminders
                if log.last_email_sent and log.last_email_sent <= (now - timedelta(hours=24)):
                    can_send = True

            if can_send:
                order._send_abandoned_cart_email(log=log)

    def action_confirm(self):
        """Mark as recovered when confirmed."""
        res = super().action_confirm()
        for order in self:
            if order.abandoned_cart_state == "abandoned" or order.abandoned_cart_log_ids:
                order.write({"abandoned_cart_state": "recovered"})
                for log in order.abandoned_cart_log_ids.filtered(lambda l: l.state != "recovered"):
                    log.write({
                        "state": "recovered",
                        "recovery_datetime": fields.Datetime.now(),
                    })
        return res
