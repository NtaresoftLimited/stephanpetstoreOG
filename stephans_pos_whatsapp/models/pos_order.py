import logging

import requests

from odoo import _, models
from odoo.exceptions import UserError
from odoo.addons.whatsapp_connector.models.res_users import normalize_whatsapp_phone

_logger = logging.getLogger(__name__)

WASENDER_URL = "https://wasenderapi.com/api/send-message"


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _whatsapp_receipt_caption(self):
        self.ensure_one()
        first_name = (self.partner_id.name or "").split(" ")[0] if self.partner_id else ""
        greeting = _("Hi %s,", first_name) if first_name else _("Hello,")
        amount = self.currency_id.format(self.amount_total) if self.currency_id else self.amount_total
        return _(
            "%(greeting)s thank you for shopping at %(shop)s.\nReceipt %(ref)s · Total %(amount)s",
            greeting=greeting,
            shop=self.config_id.name or self.company_id.name,
            ref=self.pos_reference or self.name,
            amount=amount,
        )

    def action_send_whatsapp_receipt(self, phone):
        """Send the receipt image to a WhatsApp number (called from the POS Send Receipt popup)."""
        self.ensure_one()
        e164, digits, _last9 = normalize_whatsapp_phone(phone)
        if len(digits) < 10:
            raise UserError(_("Enter a valid WhatsApp number, e.g. 0769 324 445 or +255769324445."))
        params = self.env["ir.config_parameter"].sudo()
        api_key = params.get_str("stephans_whatsapp.api_key")
        if not api_key:
            raise UserError(_("WhatsApp is not configured (system parameter stephans_whatsapp.api_key)."))

        image = self.order_receipt_generate_image()
        if not image:
            raise UserError(_("The receipt image could not be generated."))
        file_name = "Receipt-%s.jpg" % (self.pos_reference or self.name or self.id)
        attachment = self.env["ir.attachment"].sudo().create({
            "name": file_name,
            "type": "binary",
            "raw": image,
            "mimetype": "image/jpeg",
            "res_model": "pos.order",
            "res_id": self.id,
        })
        attachment.generate_access_token()
        base_url = params.get_str("web.base.url")
        image_url = "%s/web/content/%s/%s?access_token=%s" % (base_url, attachment.id, file_name, attachment.access_token)

        payload = {"to": e164, "text": self._whatsapp_receipt_caption(), "imageUrl": image_url}
        try:
            response = requests.post(
                WASENDER_URL,
                json=payload,
                headers={"Authorization": "Bearer %s" % api_key, "Content-Type": "application/json"},
                timeout=30,
            )
            body = response.json() if response.content else {}
        except (requests.RequestException, ValueError) as exc:
            _logger.warning("WhatsApp receipt for %s failed: %s", self.pos_reference, exc)
            raise UserError(_("WhatsApp could not be reached. Please try again.")) from exc
        if response.status_code >= 300 or body.get("success") is False:
            _logger.warning("WhatsApp receipt for %s rejected (%s): %s", self.pos_reference, response.status_code, body)
            raise UserError(_("WhatsApp refused the message: %s", body.get("message") or response.status_code))

        if self.partner_id and not self.partner_id.phone:
            self.partner_id.sudo().phone = e164
        if hasattr(self, "message_post"):
            self.message_post(body=_("Receipt sent on WhatsApp to %s.", e164))
        return True
