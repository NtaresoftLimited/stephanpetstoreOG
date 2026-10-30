import logging
from odoo import models, api

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = 'pos.order'

    def _safe_post_message(self, order, body):
        if hasattr(order, 'message_post'):
            try:
                order.message_post(body=body)
            except Exception:
                pass

    def action_pos_order_paid(self):
        res = super(PosOrder, self).action_pos_order_paid()
        for order in self:
            self._send_whatsapp_confirmation(order)
        return res

    def action_send_whatsapp_receipt(self):
        """Manual action to send receipt via WhatsApp"""
        for order in self:
            self._send_whatsapp_confirmation(order, force=True)

    def _send_whatsapp_confirmation(self, order, force=False):
        """Send WhatsApp receipt. If force=True, send even if no phone (will fail but log)."""
        try:
            phone = (order.partner_id.phone or order.partner_id.mobile) if order.partner_id else False
            if not order.partner_id or not phone:
                if force:
                    self._safe_post_message(order, "Failed to send WhatsApp: Customer has no phone number.")
                return

            whatsapp = self.env['whatsapp.instance'].search([('active', '=', True)], limit=1)
            if not whatsapp:
                if force:
                    self._safe_post_message(order, "Failed to send WhatsApp: No active instance.")
                return

            # Format items
            items_str = ""
            lines = order.lines
            if len(lines) <= 5:
                for line in lines:
                    prod_name = line.full_product_name or line.product_id.name
                    items_str += f"- {prod_name} x {line.qty}\n"
            else:
                items_str = f"- {len(lines)} items purchased\n"

            # Format date
            date_str = str(order.date_order)
            if hasattr(order.date_order, 'strftime'):
                date_str = order.date_order.strftime('%Y-%m-%d %H:%M')

            currency = order.currency_id.name if order.currency_id else "TZS"
            style = getattr(whatsapp, 'pos_receipt_style', 'modern') or 'modern'

            if style == 'minimal':
                msg = (
                    f"Receipt: {order.pos_reference}\n"
                    f"{date_str}\n"
                    f"{items_str}"
                    f"Total: {order.amount_total:,.0f} {currency}"
                )
            elif style == 'standard':
                msg = (
                    f"*Receipt: {order.pos_reference}*\n"
                    f"Date: {date_str}\n\n"
                    f"Items:\n{items_str}\n"
                    f"*Total: {order.amount_total:,.0f} {currency}*\n\n"
                    f"Thank you for shopping with us!"
                )
            else:
                msg = (
                    f"🐾 *Receipt from Stephan's Pet Store* 🐾\n\n"
                    f"Hello {order.partner_id.name},\n"
                    f"Thank you for your purchase! 🛍️\n\n"
                    f"🧾 *Order:* {order.pos_reference}\n"
                    f"📅 *Date:* {date_str}\n"
                    f"{items_str}\n"
                    f"💰 *Total:* {order.amount_total:,.0f} {currency}\n\n"
                    f"See you again soon!"
                )

            success, response = whatsapp.send_message(phone, msg)

            if success:
                self._safe_post_message(order, f"WhatsApp receipt sent to {phone}")
            else:
                self._safe_post_message(order, f"Failed to send WhatsApp: {response}")
                _logger.warning(f"WhatsApp send failed for POS {order.id}: {response}")

        except Exception as e:
            _logger.error(f"Failed to send WhatsApp for POS Order {order.id}: {e}")
            if force:
                self._safe_post_message(order, f"Error sending WhatsApp: {str(e)}")
