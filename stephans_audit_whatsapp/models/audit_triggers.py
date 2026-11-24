# -*- coding: utf-8 -*-
import logging
from odoo import api, fields, models, _

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        if self.env.context.get("install_mode") or self.env.context.get("migration_mode"):
            return orders
        for order in orders:
            try:
                # 1. POS Refund / Return Detection
                if order.amount_total < 0 or any(l.qty < 0 for l in order.lines):
                    currency_symbol = order.currency_id.symbol if order.currency_id else "TZS"
                    details = (
                        f"• Total Refund Amount: {order.amount_total:,.2f} {currency_symbol}\n"
                        f"• POS Config: {order.config_id.name}\n"
                        f"• Cashier: {order.user_id.name}\n"
                        f"• Customer: {order.partner_id.name if order.partner_id else 'Walk-in Customer'}\n"
                        f"• Lines:\n" + "\n".join([f"  - {line.product_id.name} (Qty: {line.qty}, Subtotal: {line.price_subtotal_incl:,.2f})" for line in order.lines if line.qty < 0])
                    )
                    self.env["audit.whatsapp.log"].audit_and_notify(
                        model_name="pos.order",
                        res_id=order.id,
                        record_name=order.pos_reference or order.name,
                        action="create",
                        details=details,
                        rule_code="pos_refund",
                        severity="high",
                    )

                # 2. High Discount Detection (> 15%)
                high_discount_lines = [l for l in order.lines if (l.discount or 0) >= 15.0]
                if high_discount_lines:
                    discount_info = "\n".join([
                        f"  - {l.product_id.name}: {l.discount}% off (Price: {l.price_unit:,.2f}, Total: {l.price_subtotal_incl:,.2f})"
                        for l in high_discount_lines
                    ])
                    details = (
                        f"• POS Config: {order.config_id.name}\n"
                        f"• Cashier: {order.user_id.name}\n"
                        f"• Total Bill: {order.amount_total:,.2f}\n"
                        f"• Discounted Items:\n{discount_info}"
                    )
                    self.env["audit.whatsapp.log"].audit_and_notify(
                        model_name="pos.order",
                        res_id=order.id,
                        record_name=order.pos_reference or order.name,
                        action="create",
                        details=details,
                        rule_code="pos_discount",
                        severity="medium",
                    )
            except Exception as e:
                _logger.warning("POS Audit check exception: %s", e)

        return orders

    def unlink(self):
        for order in self:
            try:
                self.env["audit.whatsapp.log"].audit_and_notify(
                    model_name="pos.order",
                    res_id=order.id,
                    record_name=order.pos_reference or order.name,
                    action="unlink",
                    details=f"POS Order {order.pos_reference or order.name} (Amount: {order.amount_total:,.2f}) was deleted.",
                    rule_code="pos_delete",
                    severity="high",
                )
            except Exception as e:
                _logger.warning("POS Unlink audit exception: %s", e)
        return super().unlink()


class StockQuant(models.Model):
    _inherit = "stock.quant"

    def action_apply_inventory(self):
        if self.env.context.get("install_mode") or self.env.context.get("migration_mode"):
            return super().action_apply_inventory()
        for quant in self:
            try:
                diff = (quant.inventory_quantity or quant.quantity) - quant.quantity
                if diff != 0:
                    details = (
                        f"• Product: {quant.product_id.display_name}\n"
                        f"• Location: {quant.location_id.complete_name}\n"
                        f"• On-Hand Qty: {quant.quantity:,.2f}\n"
                        f"• Counted Qty: {quant.inventory_quantity:,.2f}\n"
                        f"• Discrepancy: {'+' if diff > 0 else ''}{diff:,.2f} {quant.product_uom_id.name}"
                    )
                    self.env["audit.whatsapp.log"].audit_and_notify(
                        model_name="stock.quant",
                        res_id=quant.id,
                        record_name=quant.product_id.display_name,
                        action="write",
                        details=details,
                        rule_code="stock_inventory",
                        severity="high",
                    )
            except Exception as e:
                _logger.warning("StockQuant audit exception: %s", e)
        return super().action_apply_inventory()


class ResUsers(models.Model):
    _inherit = "res.users"

    def write(self, vals):
        if "groups_id" in vals:
            for user in self:
                try:
                    self.env["audit.whatsapp.log"].audit_and_notify(
                        model_name="res.users",
                        res_id=user.id,
                        record_name=user.name,
                        action="security",
                        details=(
                            f"• Target User: {user.name} ({user.login})\n"
                            f"• Modified by: {self.env.user.name} ({self.env.user.login})\n"
                            f"• Group modifications: {vals.get('groups_id')}"
                        ),
                        rule_code="user_security",
                        severity="high",
                    )
                except Exception as e:
                    _logger.warning("ResUsers audit exception: %s", e)
        return super().write(vals)


class ResPartner(models.Model):
    _inherit = "res.partner"

    def write(self, vals):
        if any(f in vals for f in ("bank_ids", "property_account_receivable_id", "property_account_payable_id")):
            for partner in self:
                try:
                    altered = [k for k in ("bank_ids", "property_account_receivable_id", "property_account_payable_id") if k in vals]
                    self.env["audit.whatsapp.log"].audit_and_notify(
                        model_name="res.partner",
                        res_id=partner.id,
                        record_name=partner.name,
                        action="write",
                        details=(
                            f"• Partner: {partner.name}\n"
                            f"• Altered Fields: {', '.join(altered)}\n"
                            f"• Modified by: {self.env.user.name}"
                        ),
                        rule_code="partner_bank",
                        severity="high",
                    )
                except Exception as e:
                    _logger.warning("ResPartner audit exception: %s", e)
        return super().write(vals)
