# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import hashlib
import logging
import secrets
from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class SaleOrder(models.Model):
    _inherit = "sale.order"

    abandoned_cart_token_hash = fields.Char(
        string="Recovery Token Hash (SHA-256)",
        copy=False,
        index=True,
        help="One-way cryptographic SHA-256 hash of the ephemeral recovery token.",
    )
    abandoned_cart_token_expiry = fields.Datetime(
        string="Recovery Token Expiry",
        copy=False,
        index=True,
        help="Expiration timestamp for the recovery link (48 hours validity).",
    )
    abandoned_cart_partner_id = fields.Many2one(
        "res.partner",
        string="Original Cart Customer",
        copy=False,
        help="Tracks the initial customer associated with the abandoned cart without exposing PII.",
    )
    abandoned_cart_token = fields.Char(
        string="Cart Recovery Token",
        compute="_compute_abandoned_cart_token",
        help="Ephemeral token representation (never stored in plaintext).",
    )
    abandoned_cart_state = fields.Selection(
        [
            ("active", "Active Cart"),
            ("abandoned", "Abandoned"),
            ("reminder_sent", "Reminder Sent"),
            ("recovered", "Recovered"),
            ("cancelled", "Cancelled / Expired"),
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

    def _compute_abandoned_cart_token(self):
        for order in self:
            order.abandoned_cart_token = False

    @api.depends("abandoned_cart_log_ids")
    def _compute_abandoned_cart_log_count(self):
        for order in self:
            order.abandoned_cart_log_count = len(order.abandoned_cart_log_ids)

    def _compute_cart_recovery_url(self):
        for order in self:
            order.cart_recovery_url = self._context.get("recovery_url") or False

    def _ensure_abandoned_cart_token(self):
        """Compatibility alias: ensures order has an active unexpired token hash."""
        for order in self:
            if not order.abandoned_cart_token_hash or (order.abandoned_cart_token_expiry and order.abandoned_cart_token_expiry < fields.Datetime.now()):
                order._generate_recovery_token()

    def _generate_recovery_token(self):
        """Generates a high-entropy ephemeral recovery token, stores its SHA-256 hash and 48h expiry."""
        self.ensure_one()
        raw_token = secrets.token_urlsafe(32)
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        expiry = fields.Datetime.now() + timedelta(hours=48)
        self.sudo().write({
            "abandoned_cart_token_hash": token_hash,
            "abandoned_cart_token_expiry": expiry,
        })
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url", "").rstrip("/")
        recovery_url = f"{base_url}/shop/cart/recovery/{raw_token}"
        return raw_token, recovery_url

    def _revalidate_cart_stock_and_prices(self):
        """Real-time validation: checks stock availability and recalculates unit prices and taxes."""
        self.ensure_one()
        notes = []
        for line in self.order_line:
            product = line.product_id
            product_type = getattr(product, "detailed_type", False) or getattr(product, "type", False)
            if product_type == "product":
                available_qty = max(0, product.qty_available)
                if available_qty <= 0:
                    notes.append(f"Removed '{product.display_name}' (Out of stock)")
                    line.unlink()
                    continue
                elif line.product_uom_qty > available_qty:
                    notes.append(f"Adjusted '{product.display_name}' qty from {line.product_uom_qty} to {available_qty}")
                    line.product_uom_qty = available_qty

            if line.exists():
                if hasattr(line, "_compute_price_unit"):
                    line._compute_price_unit()
                if hasattr(line, "_compute_amount"):
                    line._compute_amount()

        if hasattr(self, "_compute_amounts"):
            self._compute_amounts()
        return notes

    def action_generate_recovery_link(self):
        """Backend action for staff to generate a single-use recovery link with audit log."""
        self.ensure_one()
        if self.state not in ("draft", "sent"):
            raise UserError(_("Cannot generate recovery link for a confirmed or cancelled order."))

        raw_token, recovery_url = self._generate_recovery_token()

        # Audit log entry
        log = self.env["abandoned.cart.log"].search([
            ("order_id", "=", self.id),
            ("state", "!=", "recovered"),
        ], limit=1)
        if not log:
            log = self.env["abandoned.cart.log"].create({
                "order_id": self.id,
                "abandon_datetime": fields.Datetime.now(),
                "state": "abandoned",
                "actor": "manual",
                "user_id": self.env.uid,
            })
        log.write({
            "notes": (log.notes or "") + f"\n[{fields.Datetime.now()}] Staff {self.env.user.name} generated single-use recovery link.",
            "actor": "manual",
            "user_id": self.env.uid,
        })

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Single-Use Recovery Link Generated (Valid 48h)"),
                "message": recovery_url,
                "type": "info",
                "sticky": True,
            },
        }

    def action_view_abandoned_cart_logs(self):
        self.ensure_one()
        return {
            "name": _("Abandoned Cart Logs"),
            "type": "ir.actions.act_window",
            "res_model": "abandoned.cart.log",
            "domain": [("order_id", "=", self.id)],
            "view_mode": "list,form",
            "context": {"default_order_id": self.id},
        }

    def _send_abandoned_cart_email(self, log=None, template=None, actor="cron", user_id=None):
        """Send recovery email to customer and record audit log."""
        self.ensure_one()

        if self.abandoned_cart_state in ("recovered", "cancelled") or self.state not in ("draft", "sent"):
            _logger.info("Order %s state (%s / %s) not eligible for recovery email", self.name, self.state, self.abandoned_cart_state)
            return False

        if not self.partner_id.email:
            _logger.info("Cannot send abandoned cart email for order %s: missing email", self.name)
            return False

        # Generate fresh secure ephemeral token & URL
        raw_token, recovery_url = self._generate_recovery_token()

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
            log = self.env["abandoned.cart.log"].search([
                ("order_id", "=", self.id),
                ("state", "!=", "recovered"),
            ], limit=1)
            if not log:
                log = self.env["abandoned.cart.log"].create({
                    "order_id": self.id,
                    "abandon_datetime": fields.Datetime.now(),
                    "state": "abandoned",
                    "template_id": mail_template.id,
                    "actor": actor,
                    "user_id": user_id or (self.env.uid if actor == "manual" else False),
                })

        try:
            # Send the email with recovery_url in context
            mail_template.sudo().with_context(recovery_url=recovery_url).send_mail(
                self.id,
                force_send=True,
                raise_exception=False,
            )

            now = fields.Datetime.now()
            log.write({
                "state": "email_sent",
                "channel": "email",
                "actor": actor,
                "user_id": user_id or (self.env.uid if actor == "manual" else False),
                "last_email_sent": now,
                "emails_sent_count": log.emails_sent_count + 1,
                "template_id": mail_template.id,
                "delivery_status": "sent",
                "notes": (log.notes or "") + f"\n[{now}] Email reminder #{log.emails_sent_count + 1} dispatched via {actor}.",
            })
            self.write({"abandoned_cart_state": "reminder_sent"})
            _logger.info("Abandoned cart email sent for order %s to %s", self.name, self.partner_id.email)
            return True
        except Exception as e:
            _logger.exception("Failed to send abandoned cart email for order %s: %s", self.name, str(e))
            if log:
                log.write({
                    "delivery_status": "failed",
                    "notes": (log.notes or "") + f"\n[{fields.Datetime.now()}] Email dispatch error: {str(e)}",
                })
            return False

    def _send_abandoned_cart_whatsapp(self, log=None, actor="cron", user_id=None):
        """Send recovery message via WhatsApp with opt-in verification and retry limits."""
        self.ensure_one()

        if self.abandoned_cart_state in ("recovered", "cancelled") or self.state not in ("draft", "sent"):
            return False

        partner = self.partner_id
        phone = getattr(partner, "mobile", False) or partner.phone
        if not phone:
            _logger.info("Order %s partner has no phone for WhatsApp recovery", self.name)
            return False

        # Opt-out check
        if getattr(partner, "whatsapp_opt_out", False):
            _logger.info("Partner %s opted out of WhatsApp reminders. Skipping.", partner.name)
            return False

        if not log:
            log = self.env["abandoned.cart.log"].search([
                ("order_id", "=", self.id),
                ("state", "!=", "recovered"),
            ], limit=1)
            if not log:
                log = self.env["abandoned.cart.log"].create({
                    "order_id": self.id,
                    "abandon_datetime": fields.Datetime.now(),
                    "state": "abandoned",
                    "actor": actor,
                    "user_id": user_id or (self.env.uid if actor == "manual" else False),
                })

        ICP = self.env["ir.config_parameter"].sudo()
        max_reminders = int(ICP.get_param("stephans_abandoned_cart.max_reminders", 2))
        if log.whatsapp_sent_count >= max_reminders:
            _logger.info("Order %s reached maximum WhatsApp reminders (%s)", self.name, max_reminders)
            return False

        # Generate fresh secure ephemeral token & URL
        raw_token, recovery_url = self._generate_recovery_token()

        # Build message
        items_summary = []
        for line in self.order_line[:4]:
            qty = int(line.product_uom_qty) if line.product_uom_qty.is_integer() else line.product_uom_qty
            items_summary.append(f"• {line.product_id.display_name} (x{qty})")
        if len(self.order_line) > 4:
            items_summary.append(f"• ... and {len(self.order_line) - 4} more items")

        items_text = "\n".join(items_summary)
        currency = self.currency_id.name or "TZS"
        total_str = f"{currency} {self.amount_total:,.0f}" if currency == "TZS" else f"{currency} {self.amount_total:,.2f}"
        free_deliv_note = " (Qualifies for Free Delivery in Dar es Salaam)" if self.amount_total >= 100000 else ""

        body = (
            f"Stephan's Pet Store • Dar es Salaam\n"
            f"Hello {partner.name or 'there'},\n\n"
            f"We noticed you left some essentials in your shopping cart on stephanspetstore.co.tz:\n\n"
            f"{items_text}\n"
            f"─────────────────────────\n"
            f"Cart Total: {total_str}{free_deliv_note}\n\n"
            f"To review your items and complete checkout, tap your secure recovery link below:\n"
            f"{recovery_url}\n\n"
            f"Need help or prefer ordering directly? Reply to this message and our pet care team will assist you right away.\n\n"
            f"Reply STOP to opt out of reminders."
        )

        now = fields.Datetime.now()
        dispatch_success = False

        # Attempt dispatch via whatsapp.instance if available
        if "whatsapp.instance" in self.env:
            try:
                instance = self.env["whatsapp.instance"].sudo().get_default_instance()
                if instance and instance.api_url:
                    api_key = instance.token
                    if hasattr(instance, "_send_via_wasender") and api_key:
                        instance._send_via_wasender(phone, body, api_key)
                        dispatch_success = True
                    elif hasattr(instance, "send_message"):
                        instance.send_message(phone, body)
                        dispatch_success = True
            except Exception as e:
                _logger.warning("WhatsApp dispatch attempt error for order %s: %s", self.name, str(e))

        # Always record in audit log
        log.write({
            "channel": "whatsapp" if log.emails_sent_count == 0 else "multi",
            "actor": actor,
            "user_id": user_id or (self.env.uid if actor == "manual" else False),
            "last_whatsapp_sent": now,
            "whatsapp_sent_count": log.whatsapp_sent_count + 1,
            "delivery_status": "sent" if dispatch_success else "draft",
            "notes": (log.notes or "") + f"\n[{now}] WhatsApp reminder #{log.whatsapp_sent_count + 1} prepared/sent to {phone} via {actor}.",
        })
        self.write({"abandoned_cart_state": "reminder_sent"})
        return True

    @api.model
    def _cron_check_abandoned_carts(self):
        """Cron job: Identifies abandoned eCommerce carts and dispatches recovery notifications."""
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

        candidate_orders = self.search([
            ("state", "in", ["draft", "sent"]),
            ("website_id", "!=", False),
            ("order_line", "!=", False),
            ("partner_id.email", "!=", False),
            ("write_date", "<=", abandon_threshold),
            ("abandoned_cart_state", "not in", ["recovered", "cancelled"]),
        ])

        _logger.info("Found %d candidate abandoned cart orders for review.", len(candidate_orders))

        for order in candidate_orders:
            log = self.env["abandoned.cart.log"].search([
                ("order_id", "=", order.id),
                ("state", "!=", "recovered"),
            ], limit=1)

            if not log:
                log = self.env["abandoned.cart.log"].create({
                    "order_id": order.id,
                    "abandon_datetime": now,
                    "state": "abandoned",
                    "actor": "cron",
                })
                order.write({"abandoned_cart_state": "abandoned"})

            if log.emails_sent_count >= max_reminders:
                continue

            can_send = False
            if log.emails_sent_count == 0:
                if log.abandon_datetime and log.abandon_datetime <= (now - timedelta(minutes=reminder_delay_minutes)):
                    can_send = True
            else:
                if log.last_email_sent and log.last_email_sent <= (now - timedelta(hours=24)):
                    can_send = True

            if can_send:
                order._send_abandoned_cart_email(log=log, actor="cron")

    def action_confirm(self):
        """Single-use token revocation and status recovery on checkout confirmation."""
        res = super().action_confirm()
        for order in self:
            if order.abandoned_cart_state in ("abandoned", "reminder_sent") or order.abandoned_cart_log_ids:
                order.write({
                    "abandoned_cart_state": "recovered",
                    "abandoned_cart_token_hash": False,
                })
                for log in order.abandoned_cart_log_ids.filtered(lambda l: l.state != "recovered"):
                    log.write({
                        "state": "recovered",
                        "recovery_datetime": fields.Datetime.now(),
                        "delivery_status": "delivered",
                        "notes": (log.notes or "") + f"\n[{fields.Datetime.now()}] Cart converted to Confirmed Sale Order {order.name}. Token revoked.",
                    })
        return res

    def action_cancel(self):
        """Token revocation on cancellation."""
        res = super().action_cancel()
        for order in self:
            if order.abandoned_cart_token_hash:
                order.write({
                    "abandoned_cart_state": "cancelled",
                    "abandoned_cart_token_hash": False,
                })
                for log in order.abandoned_cart_log_ids.filtered(lambda l: l.state not in ("recovered", "cancelled")):
                    log.write({
                        "state": "cancelled",
                        "notes": (log.notes or "") + f"\n[{fields.Datetime.now()}] Order cancelled. Token revoked.",
                    })
        return res
