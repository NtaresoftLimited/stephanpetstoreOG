# -*- coding: utf-8 -*-
import hashlib
import hmac
import logging
import re
import secrets
from datetime import timedelta

from odoo import api, fields, models, _
from odoo.exceptions import AccessDenied, UserError

_logger = logging.getLogger(__name__)


def normalize_whatsapp_phone(raw_phone, default_country_code='255'):
    """
    Normalize a phone number into E.164 format (+255...), digits-only, and last-9-digits.
    Supports Tanzanian local formats (07XXXXXXXX, 7XXXXXXXX) as well as international (+254..., +968..., etc.).
    """
    if not raw_phone:
        return '', '', ''

    cleaned = str(raw_phone).strip()
    digits = re.sub(r'\D', '', cleaned)
    if not digits:
        return '', '', ''

    # Handle 00 prefix (e.g. 00255...)
    if digits.startswith('00') and len(digits) > 10:
        digits = digits[2:]

    # Tanzanian local 10-digit format: 07XXXXXXXX or 06XXXXXXXX
    if len(digits) == 10 and digits.startswith('0'):
        digits = default_country_code + digits[1:]
    # Tanzanian 9-digit format without leading 0: 7XXXXXXXX or 6XXXXXXXX
    elif len(digits) == 9 and digits[0] in ('6', '7'):
        digits = default_country_code + digits

    e164 = f"+{digits}"
    last9 = digits[-9:] if len(digits) >= 9 else digits
    return e164, digits, last9


class ResUsers(models.Model):
    _inherit = 'res.users'

    whatsapp_otp_hash = fields.Char(
        string='WhatsApp OTP Hash',
        copy=False,
        groups='base.group_system',
    )
    whatsapp_otp_expire = fields.Datetime(
        string='WhatsApp OTP Expiration',
        copy=False,
        groups='base.group_system',
    )
    whatsapp_otp_attempts = fields.Integer(
        string='WhatsApp OTP Failed Attempts',
        default=0,
        copy=False,
        groups='base.group_system',
    )

    @api.model
    def _hash_whatsapp_otp(self, user_id, otp_code):
        secret = self.env['ir.config_parameter'].sudo().get_param('database.secret', 'stephans-wa-secret')
        msg = f"{user_id}:{str(otp_code).strip()}".encode('utf-8')
        return hmac.new(secret.encode('utf-8'), msg, hashlib.sha256).hexdigest()

    @api.model
    def find_matching_partner_ids_by_phone(self, raw_phone):
        """Return all res.partner IDs whose phone or mobile matches the given phone number."""
        e164, digits, last9 = normalize_whatsapp_phone(raw_phone)
        if not last9 or len(last9) < 7:
            return []

        Partners = self.env['res.partner'].sudo()
        phone_fields = ['phone']
        if 'mobile' in Partners._fields:
            phone_fields.append('mobile')

        or_conditions = [(field, 'ilike', last9) for field in phone_fields]
        domain = [('active', '=', True), ('id', '!=', 1)]
        if len(or_conditions) > 1:
            search_domain = ['|'] * (len(or_conditions) - 1) + or_conditions + domain
        else:
            search_domain = or_conditions + domain

        candidates = Partners.search(search_domain, limit=25)
        matching = candidates.filtered(
            lambda partner: any(
                normalize_whatsapp_phone(getattr(partner, field_name, False))[2] == last9
                for field_name in phone_fields
            )
        )
        return matching.sorted(
            key=lambda partner: (-(getattr(partner, 'customer_rank', 0) or 0), partner.id)
        ).ids

    @api.model
    def find_or_create_whatsapp_portal_user(self, raw_phone, customer_name=None):
        """
        Locate an existing user/partner by phone number or auto-provision a Portal User (`base.group_portal`).
        Returns (user_sudo, e164_phone).
        """
        e164, digits, last9 = normalize_whatsapp_phone(raw_phone)
        if not digits or len(digits) < 9:
            raise UserError(_("Please enter a valid WhatsApp phone number (e.g. 0769 324 445 or +255769324445)."))

        UsersSudo = self.env['res.users'].sudo()
        PartnersSudo = self.env['res.partner'].sudo()

        partner_ids = self.find_matching_partner_ids_by_phone(raw_phone)

        # 1. Check if an active user is already linked to one of the matching partners or login
        existing_user = UsersSudo.search([
            '|',
            ('partner_id', 'in', partner_ids if partner_ids else [0]),
            ('login', 'in', [e164, digits, f"0{last9}"]),
            ('active', '=', True),
        ], order='share asc, id asc', limit=1)

        if existing_user:
            if partner_ids and existing_user.partner_id.id not in partner_ids:
                # Re-link if partner was a placeholder without orders
                pass
            if not existing_user.partner_id.phone:
                existing_user.partner_id.write({'phone': e164})
            return existing_user, e164

        # 2. Check if there is an inactive portal user for one of these partners
        inactive_user = UsersSudo.with_context(active_test=False).search([
            '|',
            ('partner_id', 'in', partner_ids if partner_ids else [0]),
            ('login', 'in', [e164, digits, f"0{last9}"]),
            ('share', '=', True),
        ], limit=1)
        if inactive_user:
            inactive_user.write({'active': True})
            return inactive_user, e164

        # 3. Pick best existing partner or create a new customer partner
        if partner_ids:
            partner = PartnersSudo.browse(partner_ids[0])
            if not partner.phone:
                partner.write({'phone': e164})
        else:
            display_name = (customer_name or '').strip() or f"Customer ({e164})"
            partner_values = {
                'name': display_name,
                'phone': e164,
                'customer_rank': 1,
            }
            if 'mobile' in PartnersSudo._fields:
                partner_values['mobile'] = e164
            partner = PartnersSudo.create(partner_values)

        # 4. Provision a Portal User (base.group_portal) linked to this partner
        portal_group = self.env.ref('base.group_portal')
        candidate_login = (partner.email or '').strip() or e164
        if UsersSudo.with_context(active_test=False).search_count([('login', '=', candidate_login)]) > 0:
            candidate_login = e164
        if UsersSudo.with_context(active_test=False).search_count([('login', '=', candidate_login)]) > 0:
            candidate_login = f"{e164}_{partner.id}"

        new_user = UsersSudo.with_context(no_reset_password=True, mail_create_nosubscribe=True).create({
            'name': partner.name or f"Customer ({e164})",
            'login': candidate_login,
            'partner_id': partner.id,
            'groups_id': [(6, 0, [portal_group.id])],
            'active': True,
        })
        _logger.info("Provisioned WhatsApp portal user id=%s (login=%s) for partner id=%s", new_user.id, new_user.login, partner.id)
        return new_user, e164

    def generate_and_send_whatsapp_otp(self, target_phone=None):
        """
        Generate a 6-digit OTP, save hash with 5-minute expiry, and send via WhatsApp.
        Returns (sent_ok, otp_code, gateway_response).
        """
        self.ensure_one()
        user_sudo = self.sudo()

        e164, _digits, _last9 = normalize_whatsapp_phone(
            target_phone
            or user_sudo.partner_id.phone
            or getattr(user_sudo.partner_id, 'mobile', False)
            or user_sudo.login
        )
        if not e164:
            raise UserError(_("No valid WhatsApp number found for this account."))

        otp_code = f"{secrets.randbelow(900000) + 100000:06d}"
        otp_hash = self._hash_whatsapp_otp(user_sudo.id, otp_code)
        expiry = fields.Datetime.now() + timedelta(minutes=5)

        user_sudo.write({
            'whatsapp_otp_hash': otp_hash,
            'whatsapp_otp_expire': expiry,
            'whatsapp_otp_attempts': 0,
        })

        customer_name = user_sudo.partner_id.name or 'Valued Customer'
        msg = (
            f"🐾 *Stephan's Pet Store Portal* 🐾\n\n"
            f"Hello {customer_name},\n"
            f"Your one-time login verification code is:\n\n"
            f"🔐 *{otp_code}*\n\n"
            f"⏳ This code expires in 5 minutes.\n"
            f"If you did not request this code, please ignore this message."
        )

        whatsapp = self.env['whatsapp.instance'].sudo().get_default_instance()
        if not whatsapp:
            return False, otp_code, "No active WhatsApp instance configured"

        success, response = whatsapp.send_message(e164, msg)
        if not success:
            _logger.warning("WhatsApp gateway did not deliver OTP to %s: %s", e164, response)
            try:
                user_sudo.partner_id.message_post(
                    body=_("Portal WhatsApp OTP generated: <b>%s</b> (Gateway status: %s)") % (otp_code, response)
                )
            except Exception:
                pass
            return False, otp_code, response

        return True, otp_code, response

    def _check_credentials(self, credential, env):
        """Extend Odoo 18 authentication to support {'type': 'whatsapp_otp', 'login': ..., 'otp': ...}."""
        try:
            return super()._check_credentials(credential, env)
        except AccessDenied:
            if not (isinstance(credential, dict) and credential.get('type') == 'whatsapp_otp' and credential.get('otp')):
                raise

            otp_input = re.sub(r'\D', '', str(credential.get('otp', '')))
            if len(otp_input) != 6:
                raise AccessDenied(_("Please enter the 6-digit verification code."))

            self.env.cr.execute(
                """
                SELECT whatsapp_otp_hash, whatsapp_otp_expire, COALESCE(whatsapp_otp_attempts, 0)
                FROM res_users
                WHERE id = %s
                """,
                [self.env.user.id],
            )
            row = self.env.cr.fetchone()
            if not row:
                raise AccessDenied()

            stored_hash, expire_dt, attempts = row
            if not stored_hash or not expire_dt:
                raise AccessDenied(_("No active verification code found. Please request a new code."))

            if attempts >= 5:
                raise AccessDenied(_("Too many failed attempts. Please request a new WhatsApp code."))

            now = fields.Datetime.now()
            if now > expire_dt:
                raise AccessDenied(_("Your verification code has expired. Please request a new code."))

            expected_hash = self._hash_whatsapp_otp(self.env.user.id, otp_input)
            if not hmac.compare_digest(stored_hash, expected_hash):
                self.env.cr.execute(
                    "UPDATE res_users SET whatsapp_otp_attempts = COALESCE(whatsapp_otp_attempts, 0) + 1 WHERE id = %s",
                    [self.env.user.id],
                )
                self.env.cr.commit()
                raise AccessDenied(_("Invalid verification code. Please check your WhatsApp and try again."))

            # OTP verified — clear it immediately to prevent replay
            self.env.cr.execute(
                """
                UPDATE res_users
                SET whatsapp_otp_hash = NULL,
                    whatsapp_otp_expire = NULL,
                    whatsapp_otp_attempts = 0
                WHERE id = %s
                """,
                [self.env.user.id],
            )

            return {
                'uid': self.env.user.id,
                'auth_method': 'whatsapp_otp',
                'mfa': 'skip',
            }
