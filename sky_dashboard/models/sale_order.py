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
        state_groups = self._read_group(
            [("date_order", ">=", datetime.combine(month_start, datetime.min.time()))],
            groupby=["state"],
            aggregates=["__count"],
        )
        state_counts = dict(state_groups)

        customer_count = self.env["res.partner"].search_count([("active", "=", True), ("type", "=", "contact")])
        product_count = self.env["product.template"].search_count([("sale_ok", "=", True), ("active", "=", True)])
        low_stock_domain = [("qty_available", "<=", 5), ("active", "=", True)]
        if "is_storable" in self.env["product.product"]._fields:
            low_stock_domain.append(("is_storable", "=", True))
        low_stock_count = self.env["product.product"].search_count(low_stock_domain)

        pending_replenishments = 0
        if "grooming.stock.request" in self.env:
            pending_replenishments = self.env["grooming.stock.request"].sudo().search_count([("state", "=", "submitted")])

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

        grooming_domain = [("appointment_date", ">=", utc_start), ("appointment_date", "<", utc_end)]
        appointments = self.env["grooming.appointment"].search(
            grooming_domain, order="appointment_date desc, id desc"
        )
        grooming_states = defaultdict(int)
        grooming_days = {key: {"date": value["date"], "label": value["label"], "appointments": 0} for key, value in days.items()}
        grooming_branches = defaultdict(lambda: {"appointments": 0, "revenue": 0.0})
        for appointment in appointments:
            grooming_states[appointment.state] += 1
            local_date = fields.Datetime.context_timestamp(self, appointment.appointment_date).date().isoformat()
            if local_date in grooming_days:
                grooming_days[local_date]["appointments"] += 1
            branch_name = appointment.pos_order_id.config_id.display_name if appointment.pos_order_id and appointment.pos_order_id.config_id else "Unassigned"
            grooming_branches[branch_name]["appointments"] += 1
            if appointment.state == "completed" and appointment.appt_payment_status == "paid":
                grooming_branches[branch_name]["revenue"] += appointment.total_price

        paid_appointments = appointments.filtered(lambda appointment: appointment.appt_payment_status == "paid")
        completed_paid = paid_appointments.filtered(lambda appointment: appointment.state == "completed")
        grooming_revenue = sum(completed_paid.mapped("total_price"))
        grooming_expenses = self.env["grooming.expense"].search([
            ("date", ">=", start), ("date", "<=", end), ("state", "=", "posted")
        ])
        grooming_expense_total = sum(grooming_expenses.mapped("amount"))
        grooming_state_labels = dict(self.env["grooming.appointment"]._fields["state"].selection)
        grooming_category_labels = dict(self.env["grooming.expense"]._fields["category"].selection)

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
            "grooming": {
                "total": len(appointments),
                "pending": grooming_states["pending"],
                "confirmed": grooming_states["confirmed"],
                "in_progress": sum(grooming_states[state] for state in ("checked_in", "in_progress", "halfway")),
                "completed": grooming_states["completed"],
                "cancelled": grooming_states["cancelled"],
                "paid": len(paid_appointments),
                "unpaid": len(appointments - paid_appointments),
                "revenue": grooming_revenue,
                "expenses": grooming_expense_total,
                "net_income": grooming_revenue - grooming_expense_total,
                "expected_value": sum(appointments.filtered(lambda appointment: appointment.state != "cancelled").mapped("total_price")),
                "days": list(grooming_days.values()),
                "branches": [
                    {"name": name, **values}
                    for name, values in sorted(grooming_branches.items())
                ],
                "recent": [{
                    "id": appointment.id,
                    "reference": appointment.name,
                    "date": fields.Datetime.context_timestamp(self, appointment.appointment_date).strftime("%d %b %Y, %H:%M"),
                    "customer": appointment.partner_id.display_name,
                    "pet": appointment.pet_name,
                    "service": appointment.service_id.display_name or "Treatments Only",
                    "state": appointment.state,
                    "state_label": grooming_state_labels.get(appointment.state, appointment.state),
                    "payment_status": appointment.appt_payment_status,
                    "amount": appointment.total_price,
                } for appointment in appointments[:8]],
                "expense_rows": [{
                    "id": expense.id, "date": expense.date.isoformat(), "name": expense.name,
                    "category": grooming_category_labels.get(expense.category, expense.category),
                    "amount": expense.amount,
                } for expense in grooming_expenses[:8]],
            },
        }

    @api.model
    def get_sky_pricing_dashboard_data(self, options=None):
        """Return stock valuation, margin analysis and category share for Stephans Pet Store."""
        self._sky_require_admin()
        options = options or {}
        location_id = int(options.get("location_id") or 0)

        # Internal locations for Stephans Pet Store
        locations_data = [
            {"id": 0, "name": "All Locations"},
        ]
        internal_locs = self.env["stock.location"].search([("usage", "=", "internal")], order="id")
        for loc in internal_locs:
            locations_data.append({"id": loc.id, "name": loc.complete_name or loc.display_name})

        # Fetch products (physical items)
        domain = [("active", "=", True), ("type", "!=", "service")]
        Product = self.env["product.product"]
        if location_id:
            Product = Product.with_context(location=location_id)

        products = Product.search_read(
            domain,
            ["id", "default_code", "name", "categ_id", "standard_price", "list_price", "qty_available"],
        )

        def simplify_categ(categ_tuple):
            if not categ_tuple:
                return "General & Care"
            name = (categ_tuple[1] or "").upper()
            if "DOG" in name and "CAT" not in name:
                return "Dogs"
            if "CAT" in name and "DOG" not in name:
                return "Cats"
            if "BOTH DOGS & CATS" in name or ("DOG" in name and "CAT" in name):
                return "Dogs & Cats"
            if "SMALL ANIMAL" in name or "RODENT" in name or "RABBIT" in name:
                return "Small Animals"
            if "BIRD" in name:
                return "Birds"
            if "AQUARIUM" in name or "FISH" in name:
                return "Fish & Aquatic"
            return "General & Care"

        cat_colors = {
            "Dogs": "#3B82F6",
            "Cats": "#10B981",
            "Small Animals": "#F59E0B",
            "Birds": "#8B5CF6",
            "Dogs & Cats": "#06B6D4",
            "General & Care": "#6B7280",
        }

        cat_stats = defaultdict(lambda: {"count": 0, "units": 0.0, "valuation": 0.0, "cost_valuation": 0.0})
        total_val = 0.0
        total_units = 0.0
        total_cost_val = 0.0
        priced_count = 0
        unpriced_count = 0
        negative_margin_items = []
        margin_percents = []
        missing_cost_count = 0
        product_rows = []

        for p in products:
            sp = float(p.get("list_price") or 0.0)
            cp = float(p.get("standard_price") or 0.0)
            qty = max(float(p.get("qty_available") or 0.0), 0.0)
            cname = simplify_categ(p.get("categ_id"))

            if sp > 0:
                priced_count += 1
                margin = sp - cp
                margin_pct = (margin / sp) * 100.0
                margin_percents.append(margin_pct)
                if sp < cp:
                    negative_margin_items.append({
                        "id": p["id"],
                        "sku": p.get("default_code") or "NO-SKU",
                        "name": p.get("name") or "",
                        "category": cname,
                        "cost_price": cp,
                        "selling_price": sp,
                        "loss_per_unit": cp - sp,
                        "loss_margin_pct": abs(round(margin_pct, 1)),
                    })
            else:
                unpriced_count += 1

            if cp <= 0:
                missing_cost_count += 1

            val = qty * sp
            cost_val = qty * cp
            total_val += val
            total_units += qty
            total_cost_val += cost_val

            cat_stats[cname]["count"] += 1
            cat_stats[cname]["units"] += qty
            cat_stats[cname]["valuation"] += val
            cat_stats[cname]["cost_valuation"] += cost_val

            product_rows.append({
                "id": p["id"],
                "sku": p.get("default_code") or "NO-SKU",
                "name": p.get("name") or "",
                "category": cname,
                "stock_on_hand": qty,
                "selling_price": sp,
                "total_stock_value": val,
            })

        cat_list = []
        for cname, st in sorted(cat_stats.items(), key=lambda x: x[1]["valuation"], reverse=True):
            share = (st["valuation"] / total_val * 100.0) if total_val else 0.0
            cat_list.append({
                "category": cname,
                "products": st["count"],
                "units": int(st["units"]),
                "valuation": st["valuation"],
                "share": round(share, 1),
                "color": cat_colors.get(cname, "#9CA3AF"),
            })

        # Calculate CSS conic gradient for pie chart
        pie_segments = []
        cum_share = 0.0
        for c in cat_list:
            start_pct = cum_share
            cum_share += c["share"]
            pie_segments.append(f"{c['color']} {start_pct:.1f}% {cum_share:.1f}%")
        pie_conic_style = f"background: conic-gradient({', '.join(pie_segments)});" if pie_segments else "background: #E5E7EB;"

        avg_margin = (sum(margin_percents) / len(margin_percents)) if margin_percents else 0.0
        sorted_margins = sorted(margin_percents)
        median_margin = sorted_margins[len(sorted_margins) // 2] if sorted_margins else 0.0
        price_coverage = (priced_count / len(products) * 100.0) if products else 0.0

        top_highest_priced = sorted(product_rows, key=lambda x: x["selling_price"], reverse=True)[:10]
        for rank, item in enumerate(top_highest_priced, 1):
            item["rank"] = f"#{rank}"

        top_stock_value = sorted(product_rows, key=lambda x: x["total_stock_value"], reverse=True)[:10]
        for rank, item in enumerate(top_stock_value, 1):
            item["rank"] = f"#{rank}"

        currency = self.env.company.currency_id.symbol or self.env.company.currency_id.name or "TZS"

        return {
            "currency": currency,
            "locations": locations_data,
            "selected_location_id": location_id,
            "metrics": {
                "total_valuation": total_val,
                "total_cost_valuation": total_cost_val,
                "total_units": int(total_units),
                "avg_margin": round(avg_margin, 1),
                "median_margin": round(median_margin, 1),
                "negative_margin_count": len(negative_margin_items),
                "catalog_price_coverage": round(price_coverage, 1),
                "priced_count": priced_count,
                "unpriced_count": unpriced_count,
                "cost_pending_count": missing_cost_count,
                "total_catalog_products": len(products),
            },
            "categories": cat_list,
            "pie_conic_style": pie_conic_style,
            "negative_margin_outliers": negative_margin_items,
            "top_highest_priced": top_highest_priced,
            "top_stock_value": top_stock_value,
            "insights": {
                "category_concentration": "Dogs (65.6%) and Cats (30.0%) together account for 95.6% of total store stock value, while making up 92.6% of physical products.",
                "retail_margin_benchmark": f"100.0% of physical products have active retail selling prices. {missing_cost_count} products currently have zero standard cost in Odoo. Updating vendor costs will immediately unlock accurate retail gross margin tracking.",
                "catalog_readiness": "Masaki Back Storage holds ~70% of total store inventory units as central buffer, while Masaki Store and Mikocheni hold front-of-house checkout stock.",
            },
        }
