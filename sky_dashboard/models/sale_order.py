from collections import defaultdict
from datetime import datetime, time, timedelta

import pytz
from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _sky_require_admin(self):
        if not self.env.is_admin() and not self.env.user.has_group("base.group_system"):
            raise AccessError(_("The SKY dashboard is restricted to administrators."))

    def _sky_week_dates(self, options):
        today = fields.Date.context_today(self)
        default_start = today - timedelta(days=today.weekday())
        start = fields.Date.to_date(options.get("date_start")) if options.get("date_start") else default_start
        end = fields.Date.to_date(options.get("date_end")) if options.get("date_end") else start + timedelta(days=6)
        if end < start:
            raise ValidationError(_("The end date must be on or after the start date."))
        if (end - start).days > 92:
            raise ValidationError(_("Choose a date range of 93 days or fewer."))
        return start, end

    def _sky_utc_boundaries(self, start, end):
        timezone = pytz.timezone(self.env.user.tz or "UTC")
        start_local = timezone.localize(datetime.combine(start, time.min))
        end_local = timezone.localize(datetime.combine(end + timedelta(days=1), time.min))
        return (
            start_local.astimezone(pytz.UTC).replace(tzinfo=None),
            end_local.astimezone(pytz.UTC).replace(tzinfo=None),
        )

    @api.model
    def get_sky_dashboard_data(self, options=None):
        """Return the admin-only SKY overview, including POS sales and expenses."""
        self._sky_require_admin()
        options = options or {}
        today = fields.Date.context_today(self)
        month_start = today.replace(day=1)
        next_month = month_start + relativedelta(months=1)
        month_domain = [
            ("date_order", ">=", datetime.combine(month_start, datetime.min.time())),
            ("date_order", "<", datetime.combine(next_month, datetime.min.time())),
            ("state", "in", ["sale", "done"]),
        ]

        monthly_orders = self.search(month_domain)
        recent_orders = self.search([("state", "!=", "cancel")], order="date_order desc", limit=6)
        state_groups = self.read_group(
            [("date_order", ">=", datetime.combine(month_start, datetime.min.time()))],
            ["state"], ["state"],
        )
        state_counts = {group["state"]: group.get("state_count", 0) for group in state_groups}

        customer_count = self.env["res.partner"].search_count([("active", "=", True), ("type", "=", "contact")])
        product_count = self.env["product.template"].search_count([("sale_ok", "=", True), ("active", "=", True)])
        low_stock_domain = [("qty_available", "<=", 5), ("active", "=", True)]
        if "is_storable" in self.env["product.product"]._fields:
            low_stock_domain.append(("is_storable", "=", True))
        low_stock_count = self.env["product.product"].search_count(low_stock_domain)

        pending_replenishments = 0
        if "grooming.stock.request" in self.env:
            pending_replenishments = self.env["grooming.stock.request"].search_count([("state", "=", "submitted")])

        start, end = self._sky_week_dates(options)
        utc_start, utc_end = self._sky_utc_boundaries(start, end)
        configs = self.env["pos.config"].search([("active", "=", True)], order="name")
        config_id = int(options.get("config_id") or 0)
        if config_id and config_id not in configs.ids:
            raise ValidationError(_("The selected Point of Sale is not available."))

        pos_domain = [
            ("date_order", ">=", utc_start), ("date_order", "<", utc_end),
            ("state", "in", ["paid", "done", "invoiced"]),
        ]
        if config_id:
            pos_domain.append(("config_id", "=", config_id))
        pos_orders = self.env["pos.order"].search(pos_domain, order="date_order desc")

        days = {}
        cursor = start
        while cursor <= end:
            days[cursor.isoformat()] = {"date": cursor.isoformat(), "label": cursor.strftime("%a %d"), "sales": 0.0, "expenses": 0.0, "orders": 0}
            cursor += timedelta(days=1)
        branches = defaultdict(lambda: {"sales": 0.0, "gross_sales": 0.0, "returns": 0.0, "expenses": 0.0, "orders": 0, "items": 0.0})
        payments = defaultdict(float)
        gross_sales = return_amount = items_sold = 0.0
        for order in pos_orders:
            local_date = fields.Datetime.context_timestamp(self, order.date_order).date().isoformat()
            amount = order.amount_total
            gross_sales += max(amount, 0.0)
            return_amount += abs(min(amount, 0.0))
            items = sum(order.lines.mapped("qty"))
            items_sold += items
            branch = branches[order.config_id.id]
            branch.update({
                "name": order.config_id.display_name,
                "sales": branch["sales"] + amount,
                "gross_sales": branch["gross_sales"] + max(amount, 0.0),
                "returns": branch["returns"] + abs(min(amount, 0.0)),
                "orders": branch["orders"] + 1,
                "items": branch["items"] + items,
            })
            if local_date in days:
                days[local_date]["sales"] += amount
                days[local_date]["orders"] += 1
            for payment in order.payment_ids:
                payments[payment.payment_method_id.name] += payment.amount

        expenses = self.env["pos.store.expense"] if "pos.store.expense" in self.env else False
        expense_records = expenses.browse() if expenses else []
        if expenses:
            expense_domain = [("date", ">=", start), ("date", "<=", end), ("state", "in", ["approved", "paid"])]
            if config_id:
                expense_domain.append(("pos_config_id", "=", config_id))
            expense_records = expenses.search(expense_domain, order="date desc, id desc")
            for expense in expense_records:
                date_key = expense.date.isoformat()
                if date_key in days:
                    days[date_key]["expenses"] += expense.amount
                branch = branches[expense.pos_config_id.id]
                branch.setdefault("name", expense.pos_config_id.display_name)
                branch["expenses"] += expense.amount

        net_sales = sum(pos_orders.mapped("amount_total"))
        expense_total = sum(expense_records.mapped("amount")) if expenses else 0.0
        branch_rows = []
        for branch_id, values in branches.items():
            values.update({"id": branch_id, "net_after_expenses": values["sales"] - values["expenses"]})
            branch_rows.append(values)
        branch_rows.sort(key=lambda row: row["name"])

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
                "confirmed": state_counts.get("sale", 0), "done": state_counts.get("done", 0),
                "cancelled": state_counts.get("cancel", 0),
            },
            "recent_orders": [{
                "id": order.id, "name": order.name, "customer": order.partner_id.display_name,
                "date": fields.Datetime.context_timestamp(self, order.date_order).strftime("%d %b %Y"),
                "state": order.state, "amount": order.amount_total,
            } for order in recent_orders],
            "pos_configs": [{"id": config.id, "name": config.display_name} for config in configs],
            "weekly": {
                "date_start": start.isoformat(), "date_end": end.isoformat(), "config_id": config_id,
                "gross_sales": gross_sales, "returns": return_amount, "net_sales": net_sales,
                "expenses": expense_total, "net_after_expenses": net_sales - expense_total,
                "orders": len(pos_orders), "items": items_sold,
                "average_order": net_sales / len(pos_orders) if pos_orders else 0.0,
                "days": list(days.values()), "branches": branch_rows,
                "payments": [{"name": name, "amount": amount} for name, amount in sorted(payments.items())],
                "expense_rows": [{
                    "id": expense.id, "name": expense.name, "date": expense.date.isoformat(),
                    "branch": expense.pos_config_id.display_name,
                    "category": expense.category_id.display_name, "description": expense.description,
                    "state": expense.state, "amount": expense.amount,
                } for expense in expense_records[:20]],
            },
        }
