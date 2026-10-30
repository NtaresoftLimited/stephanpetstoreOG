from datetime import datetime

from dateutil.relativedelta import relativedelta

from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.model
    def get_sky_dashboard_data(self):
        """Return the compact data set used by the SKY client action."""
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)
        next_month = month_start + relativedelta(months=1)
        month_domain = [
            ("date_order", ">=", datetime.combine(month_start, datetime.min.time())),
            ("date_order", "<", datetime.combine(next_month, datetime.min.time())),
            ("state", "in", ["sale", "done"]),
        ]

        monthly_orders = self.search(month_domain)
        recent_orders = self.search(
            [("state", "!=", "cancel")], order="date_order desc", limit=6
        )

        try:
            state_groups = self._read_group(
                [("date_order", ">=", datetime.combine(month_start, datetime.min.time()))],
                groupby=["state"],
                aggregates=["__count"],
            )
            state_counts = {state: count for state, count in state_groups}
        except Exception:
            state_groups = self.read_group(
                [("date_order", ">=", datetime.combine(month_start, datetime.min.time()))],
                ["state"],
                ["state"],
            )
            state_counts = {group["state"]: group.get("state_count", 0) for group in state_groups}

        customer_count = self.env["res.partner"].search_count(
            [("active", "=", True), ("type", "=", "contact")]
        )

        product_count = self.env["product.template"].search_count(
            [("sale_ok", "=", True), ("active", "=", True)]
        )

        low_stock_domain = [("qty_available", "<=", 5), ("active", "=", True)]
        if "is_storable" in self.env["product.product"]._fields:
            low_stock_domain.append(("is_storable", "=", True))
        low_stock_count = self.env["product.product"].search_count(low_stock_domain)

        pending_replenishments = 0
        if "grooming.stock.request" in self.env:
            try:
                pending_replenishments = self.env["grooming.stock.request"].search_count([("state", "=", "submitted")])
            except Exception:
                pending_replenishments = 0

        company = self.env.company
        return {
            "currency": company.currency_id.symbol or company.currency_id.name,
            "monthly_revenue": sum(monthly_orders.mapped("amount_total")),
            "monthly_orders": len(monthly_orders),
            "monthly_activity": sum(state_counts.values()),
            "customers": customer_count,
            "products": product_count,
            "low_stock": low_stock_count,
            "pending_replenishments": pending_replenishments,
            "states": {
                "quotation": state_counts.get("draft", 0) + state_counts.get("sent", 0),
                "confirmed": state_counts.get("sale", 0),
                "done": state_counts.get("done", 0),
                "cancelled": state_counts.get("cancel", 0),
            },
            "recent_orders": [
                {
                    "id": order.id,
                    "name": order.name,
                    "customer": order.partner_id.display_name,
                    "date": fields.Datetime.context_timestamp(self, order.date_order).strftime("%d %b %Y"),
                    "state": order.state,
                    "amount": order.amount_total,
                }
                for order in recent_orders
            ],
        }
