# -*- coding: utf-8 -*-
import logging
import requests
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from odoo.addons.whatsapp_connector.models.res_users import get_config_str, normalize_whatsapp_phone

_logger = logging.getLogger(__name__)

WASENDER_URL = "https://wasenderapi.com/api/send-message"


class AuditWhatsAppLog(models.Model):
    _name = "audit.whatsapp.log"
    _description = "Audit Trail & WhatsApp Alert Log"
    _order = "timestamp desc, id desc"

    name = fields.Char(string="Summary", required=True, index=True)
    rule_id = fields.Many2one("audit.whatsapp.rule", string="Triggered Rule", ondelete="set null", index=True)
    model_name = fields.Char(string="Model Name", index=True)
    res_id = fields.Integer(string="Record ID", index=True)
    record_name = fields.Char(string="Record Reference / Name")
    action = fields.Selection([
        ("create", "Created"),
        ("write", "Modified"),
        ("unlink", "Deleted"),
        ("security", "Security Alert"),
    ], string="Action", default="write", required=True)

    severity = fields.Selection([
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High / Critical"),
    ], string="Severity", default="medium", required=True, index=True)

    user_id = fields.Many2one("res.users", string="Executed By", default=lambda self: self.env.user, index=True)
    timestamp = fields.Datetime(string="Timestamp", default=fields.Datetime.now, required=True, index=True)
    details = fields.Text(string="Audit Event Details")

    whatsapp_status = fields.Selection([
        ("pending", "Pending"),
        ("sent", "Sent"),
        ("failed", "Failed"),
        ("skipped", "Skipped"),
    ], string="WhatsApp Status", default="pending", index=True)

    whatsapp_recipient = fields.Char(string="Recipients")
    whatsapp_response = fields.Text(string="WhatsApp Gateway Response")

    @api.model
    def _dispatch_whatsapp(self, phone, body):
        """
        Sends WhatsApp text via WASenderAPI or UltraMsg gateway.
        Returns (success: bool, response_info: str)
        """
        if not phone or not body:
            return False, "Empty phone or body"

        e164, digits, _ = normalize_whatsapp_phone(phone)
        if len(digits) < 9:
            return False, f"Invalid phone format: {phone}"

        # 1. Primary: WASenderAPI via system parameters
        params = self.env["ir.config_parameter"].sudo()
        wasender_key = get_config_str(self.env, "stephans_whatsapp.api_key")
        if wasender_key:
            headers = {
                "Authorization": f"Bearer {wasender_key}",
                "Content-Type": "application/json",
                "User-Agent": "Odoo/20.0 (Stephans-Audit)",
            }
            payload = {
                "to": e164,
                "text": body,
            }
            try:
                resp = requests.post(WASENDER_URL, json=payload, headers=headers, timeout=12)
                res_json = resp.json() if resp.content else {}
                if resp.status_code in (200, 201) and res_json.get("success") is not False:
                    return True, "WASender sent successfully"
                return False, f"WASender HTTP {resp.status_code}: {res_json}"
            except Exception as exc:
                _logger.warning("WASenderAPI error for audit alert to %s: %s", e164, exc)

        # 2. Secondary: UltraMsg instance if available
        if "whatsapp.instance" in self.env:
            try:
                wa_instance = self.env["whatsapp.instance"].sudo().get_default_instance()
                if wa_instance:
                    ok, res = wa_instance.send_message(e164, body)
                    return ok, str(res)
            except Exception as wa_exc:
                _logger.warning("UltraMsg error for audit alert: %s", wa_exc)

        return False, "No active WhatsApp gateway configuration found"

    @api.model
    def audit_and_notify(self, model_name, res_id, record_name, action, details, rule_code=None, severity=None):
        """
        Main entry point for auditing an action and dispatching WhatsApp alerts.
        Wrapped in comprehensive safety checks so it never raises exceptions to the caller.
        """
        try:
            rule_obj = self.env["audit.whatsapp.rule"].sudo()
            matched_rule = False

            # Search rule by code first
            if rule_code:
                matched_rule = rule_obj.search([("code", "=", rule_code), ("active", "=", True)], limit=1)

            # Fallback search by model and action
            if not matched_rule:
                ir_model = self.env["ir.model"].sudo().search([("model", "=", model_name)], limit=1)
                if ir_model:
                    matched_rule = rule_obj.search([
                        ("model_id", "=", ir_model.id),
                        ("active", "=", True),
                        ("action_type", "in", (action, "all")),
                    ], limit=1)

            final_severity = severity or (matched_rule.severity if matched_rule else "medium")
            user = self.env.user
            time_str = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

            summary = f"{action.upper()} on {model_name} #{res_id}"
            if record_name:
                summary = f"{action.upper()}: {record_name}"

            log_vals = {
                "name": summary,
                "rule_id": matched_rule.id if matched_rule else False,
                "model_name": model_name,
                "res_id": res_id or 0,
                "record_name": record_name or f"#{res_id}",
                "action": action if action in dict(self._fields["action"].selection) else "write",
                "severity": final_severity,
                "user_id": user.id,
                "timestamp": fields.Datetime.now(),
                "details": details or "",
                "whatsapp_status": "skipped",
            }

            if matched_rule and matched_rule.send_whatsapp:
                recipients = matched_rule.get_normalized_recipients()
                if recipients:
                    body = matched_rule.alert_template.format(
                        rule_name=matched_rule.name,
                        model=matched_rule.model_id.name or model_name,
                        record=record_name or f"#{res_id}",
                        action=action.upper(),
                        user=user.name,
                        time=time_str,
                        severity=final_severity.upper(),
                        details=details or "N/A",
                    )
                    responses = []
                    all_sent = True
                    for phone in recipients:
                        ok, info = self._dispatch_whatsapp(phone, body)
                        if not ok:
                            all_sent = False
                        responses.append(f"{phone}: {info}")

                    log_vals["whatsapp_status"] = "sent" if all_sent else "failed"
                    log_vals["whatsapp_recipient"] = ", ".join(recipients)
                    log_vals["whatsapp_response"] = "\n".join(responses)
                else:
                    log_vals["whatsapp_status"] = "skipped"
                    log_vals["whatsapp_response"] = "Rule has no valid recipients"
            else:
                log_vals["whatsapp_status"] = "skipped"
                log_vals["whatsapp_response"] = "WhatsApp alert disabled for this rule or no rule matched"

            log_record = self.sudo().create(log_vals)
            return log_record

        except Exception as exc:
            _logger.error("Error creating audit log or sending WhatsApp alert: %s", exc, exc_info=True)
            return False

    def action_resend_whatsapp(self):
        self.ensure_one()
        rule = self.rule_id
        if not rule:
            raise UserError(_("No linked rule found for this audit log."))
        recipients = rule.get_normalized_recipients()
        if not recipients:
            raise UserError(_("No recipients configured in linked rule."))

        time_str = (self.timestamp or fields.Datetime.now()).strftime("%Y-%m-%d %H:%M:%S UTC")
        body = rule.alert_template.format(
            rule_name=rule.name,
            model=rule.model_id.name or self.model_name or "N/A",
            record=self.record_name or f"#{self.res_id}",
            action=self.action.upper(),
            user=self.user_id.name or "System",
            time=time_str,
            severity=(self.severity or "medium").upper(),
            details=self.details or "N/A",
        )

        responses = []
        all_sent = True
        for phone in recipients:
            ok, info = self._dispatch_whatsapp(phone, body)
            if not ok:
                all_sent = False
            responses.append(f"{phone}: {info}")

        self.write({
            "whatsapp_status": "sent" if all_sent else "failed",
            "whatsapp_recipient": ", ".join(recipients),
            "whatsapp_response": "\n".join(responses),
        })
        return True
