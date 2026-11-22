# -*- coding: utf-8 -*-
import logging

from odoo import _, fields, http
from odoo.exceptions import AccessDenied, UserError
from odoo.http import request
from odoo.addons.web.controllers.utils import ensure_db
from odoo.addons.whatsapp_connector.models.res_users import get_config_str

try:  # Odoo 20: session authentication is a module-level function
    from odoo.http.session import authenticate as session_authenticate
except ImportError:  # Odoo 18 fallback
    session_authenticate = None

_logger = logging.getLogger(__name__)


class PawPointsPopupController(http.Controller):
    """JSON-RPC endpoints powering the inline Apple-frosted Paw Points WhatsApp pop-up."""

    SUPPORT_WHATSAPP = "+255 769 324 445"

    @staticmethod
    def _clear_wa_session():
        for key in ("wa_auth_user_id", "wa_auth_login", "wa_auth_phone"):
            request.session.pop(key, None)

    @staticmethod
    def _authenticate(credential):
        if session_authenticate:
            return session_authenticate(request.session, request.env, credential)
        return request.session.authenticate(request.db, credential)

    @staticmethod
    def _partner_paw_points(partner):
        today = fields.Date.context_today(request.env.user)
        partner_ids = list({partner.id, partner.commercial_partner_id.id})
        cards = request.env["loyalty.card"].sudo().search([
            ("partner_id", "in", partner_ids),
            ("program_id.active", "=", True),
            ("program_id.program_type", "=", "loyalty"),
            "|", ("expiration_date", "=", False), ("expiration_date", ">=", today),
        ])
        return sum(cards.mapped("points")) if cards else 0.0

    @http.route("/paw_points/popup/send_otp", type="jsonrpc", auth="public", website=True, sitemap=False)
    def send_otp(self, phone="", resend=False, marketing_opt_in=True, **_kw):
        ensure_db()
        Users = request.env["res.users"].sudo()

        target_phone = (request.session.get("wa_auth_phone") or phone) if resend else phone
        target_phone = (target_phone or "").strip()
        if not target_phone:
            return {"ok": False, "error": _("Please enter your phone number.")}

        try:
            if not request.env["whatsapp.instance"].sudo().get_default_instance():
                return {
                    "ok": False,
                    "error": _(
                        "WhatsApp verification is temporarily unavailable. Please sign in with email "
                        "or message us on WhatsApp at %s.",
                        self.SUPPORT_WHATSAPP,
                    ),
                }

            user_sudo, e164_phone = Users.find_or_create_whatsapp_portal_user(target_phone)
            request.session["wa_auth_user_id"] = user_sudo.id
            request.session["wa_auth_login"] = user_sudo.login
            request.session["wa_auth_phone"] = e164_phone
            request.session["wa_auth_opt_in"] = bool(marketing_opt_in)

            wait = user_sudo.whatsapp_otp_resend_wait()
            if wait:
                return {
                    "ok": True,
                    "phone": e164_phone,
                    "resend_wait": int(wait),
                    "message": _(
                        "A code was already sent to %(phone)s. You can request a new one in %(sec)s seconds.",
                        phone=e164_phone,
                        sec=wait,
                    ),
                }

            sent_ok, otp_code, gateway_res = user_sudo.generate_and_send_whatsapp_otp(target_phone=e164_phone)
            if sent_ok:
                return {
                    "ok": True,
                    "phone": e164_phone,
                    "resend_wait": int(user_sudo.whatsapp_otp_resend_wait() or 30),
                    "message": _("We sent a 6-digit verification code via WhatsApp to %s.", e164_phone),
                }

            allow_offline_demo = get_config_str(
                request.env, "whatsapp_connector.demo_show_otp_when_gateway_offline", "False"
            ) == "True"
            if allow_offline_demo:
                return {
                    "ok": True,
                    "phone": e164_phone,
                    "resend_wait": 30,
                    "message": _("WhatsApp gateway is offline (provider subscription renewal pending). Your verification code is: %s", otp_code),
                    "demo_code": otp_code,
                }

            self._clear_wa_session()
            _logger.warning("Paw Points Popup: WhatsApp OTP not delivered to %s: %s", e164_phone, gateway_res)
            return {
                "ok": False,
                "error": _(
                    "We couldn't send the WhatsApp code right now. Please check the number and try again."
                ),
            }
        except UserError as e:
            return {"ok": False, "error": e.args[0] if e.args else str(e)}
        except Exception:
            _logger.exception("Paw Points Popup: send_otp error")
            return {"ok": False, "error": _("Unable to send WhatsApp code right now. Please try again.")}

    @http.route("/paw_points/popup/verify_otp", type="jsonrpc", auth="public", website=True, sitemap=False)
    def verify_otp(self, otp="", **_kw):
        ensure_db()
        otp_code = (otp or "").strip()
        login = request.session.get("wa_auth_login")

        if not login:
            return {
                "ok": False,
                "expired": True,
                "error": _("Your verification session expired. Please enter your number again."),
            }
        if not otp_code:
            return {"ok": False, "error": _("Please enter the 6-digit verification code.")}

        try:
            credential = {"type": "whatsapp_otp", "login": login, "otp": otp_code}
            auth_info = self._authenticate(credential)
            self._clear_wa_session()
            request.session.pop("wa_auth_opt_in", None)

            uid = auth_info.get("uid") if isinstance(auth_info, dict) else auth_info
            user = request.env["res.users"].sudo().browse(uid)
            partner = user.partner_id

            points = self._partner_paw_points(partner)
            points_value = int(points * 50)
            points_formatted = f"{int(points):,}" if points == int(points) else f"{points:,.1f}"
            progress_remainder = points % 100
            if points >= 100:
                progress_pct = 100
            elif progress_remainder > 0:
                progress_pct = min(100, int((progress_remainder / 100.0) * 100))
            else:
                progress_pct = 0

            return {
                "ok": True,
                "points": points,
                "points_formatted": points_formatted,
                "points_value": points_value,
                "points_value_formatted": f"{points_value:,}",
                "progress_pct": progress_pct,
                "can_redeem": points >= 100,
                "partner_name": partner.name or "",
                "partner_phone": partner.phone or getattr(partner, "mobile", False) or "",
                "partner_email": partner.email or "",
            }
        except AccessDenied as e:
            return {
                "ok": False,
                "error": e.args[0] if e.args and e.args[0] else _("Invalid or expired verification code."),
            }
        except Exception:
            _logger.exception("Paw Points Popup: verify_otp error")
            return {"ok": False, "error": _("Verification failed. Please check the code and try again.")}

    @http.route("/paw_points/popup/reset", type="jsonrpc", auth="public", website=True, sitemap=False)
    def reset_session(self, **_kw):
        self._clear_wa_session()
        return {"ok": True}
