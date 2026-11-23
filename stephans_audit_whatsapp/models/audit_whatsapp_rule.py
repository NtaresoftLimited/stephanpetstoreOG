# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.whatsapp_connector.models.res_users import normalize_whatsapp_phone

_logger = logging.getLogger(__name__)


class AuditWhatsAppRule(models.Model):
    _name = "audit.whatsapp.rule"
    _description = "Audit WhatsApp Rule"
    _order = "name"

    name = fields.Char(string="Rule Name", required=True)
    code = fields.Char(string="Rule Code", index=True, help="Unique identifier for built-in hooks (e.g., pos_refund)")
    active = fields.Boolean(default=True)
    send_whatsapp = fields.Boolean(
        string="Send WhatsApp Notification",
        default=True,
        help="If unchecked, events will only be recorded in the audit log without sending WhatsApp alerts.",
    )

    model_id = fields.Many2one("ir.model", string="Monitored Model", ondelete="cascade", required=True)
    model_name = fields.Char(related="model_id.model", string="Model Technical Name", store=True)

    action_type = fields.Selection([
        ("all", "Any Action"),
        ("create", "Record Created"),
        ("write", "Record Modified"),
        ("unlink", "Record Deleted"),
    ], string="Trigger Action", default="write", required=True)

    severity = fields.Selection([
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High / Critical"),
    ], string="Alert Severity", default="medium", required=True)

    monitored_field_ids = fields.Many2many(
        "ir.model.fields",
        string="Monitored Fields",
        domain="[('model_id', '=', model_id)]",
        help="Only trigger when one of these specific fields is modified. Leave empty to monitor all fields.",
    )

    recipient_phones = fields.Char(
        string="Recipient WhatsApp Numbers",
        required=True,
        help="Comma-separated phone numbers, e.g. +255769324445, 0712345678",
    )

    alert_template = fields.Text(
        string="WhatsApp Message Template",
        required=True,
        default=(
            "🚨 *AUDIT ALERT: {rule_name}*\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "• *Model:* {model}\n"
            "• *Record:* {record}\n"
            "• *Action:* {action}\n"
            "• *User:* {user}\n"
            "• *Time:* {time}\n"
            "• *Severity:* {severity}\n"
            "━━━━━━━━━━━━━━━━━━━━\n"
            "📝 *Details:*\n{details}"
        ),
        help="Available placeholders: {rule_name}, {model}, {record}, {action}, {user}, {time}, {severity}, {details}",
    )

    log_count = fields.Integer(string="Audit Logs Count", compute="_compute_log_count")

    def _compute_log_count(self):
        log_obj = self.env["audit.whatsapp.log"]
        for rule in self:
            rule.log_count = log_obj.search_count([("rule_id", "=", rule.id)])

    def action_view_logs(self):
        self.ensure_one()
        return {
            "name": _("Audit Logs: %s", self.name),
            "type": "ir.actions.act_window",
            "res_model": "audit.whatsapp.log",
            "view_mode": "list,form",
            "domain": [("rule_id", "=", self.id)],
            "context": {"default_rule_id": self.id},
        }

    def get_normalized_recipients(self):
        self.ensure_one()
        phones = []
        raw_list = [p.strip() for p in (self.recipient_phones or "").split(",") if p.strip()]
        for raw in raw_list:
            e164, digits, _ = normalize_whatsapp_phone(raw)
            if len(digits) >= 9:
                phones.append(e164)
            else:
                _logger.warning("Invalid phone format in rule %s: %s", self.name, raw)
        return phones

    def action_send_test_alert(self):
        self.ensure_one()
        recipients = self.get_normalized_recipients()
        if not recipients:
            raise UserError(_("No valid recipient phone numbers configured for this rule."))

        time_str = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")
        test_body = self.alert_template.format(
            rule_name=self.name,
            model=self.model_id.name or self.model_name or "N/A",
            record="TEST-RECORD #001",
            action="TEST_VERIFICATION",
            user=self.env.user.name,
            time=time_str,
            severity=(self.severity or "medium").upper(),
            details="This is a test notification confirming that Stephans Odoo 20 WhatsApp Audit alerts are functioning properly.",
        )

        log_model = self.env["audit.whatsapp.log"]
        results = []
        for phone in recipients:
            ok, response_msg = log_model._dispatch_whatsapp(phone, test_body)
            results.append(f"{phone}: {'SENT' if ok else 'FAILED (' + str(response_msg) + ')'}")

        # Record test entry in log
        log_model.create({
            "name": f"Test Alert: {self.name}",
            "rule_id": self.id,
            "model_name": self.model_name or "audit.whatsapp.rule",
            "res_id": self.id,
            "record_name": self.name,
            "action": "security",
            "severity": "low",
            "details": f"Test verification executed by {self.env.user.name}.\n" + "\n".join(results),
            "whatsapp_status": "sent" if all("SENT" in r for r in results) else "failed",
            "whatsapp_recipient": ", ".join(recipients),
            "whatsapp_response": "\n".join(results),
        })

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Test Alert Result"),
                "message": "\n".join(results),
                "sticky": True,
                "type": "info" if all("SENT" in r for r in results) else "warning",
            },
        }
