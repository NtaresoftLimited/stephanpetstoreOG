from datetime import datetime, time, timedelta

import pytz

from odoo import _, api, fields, models
from odoo.exceptions import AccessError, ValidationError


class LucyDashboard(models.AbstractModel):
    _name = "lucy.dashboard"
    _description = "LuCy Dashboard Service"

    def _require_admin(self):
        if not self.env.is_admin() and not self.env.user.has_group("base.group_system"):
            raise AccessError(_("LuCy is restricted to administrators."))

    def _date_range(self, options):
        today = fields.Date.context_today(self)
        start = fields.Date.to_date(options.get("date_start")) if options.get("date_start") else today - timedelta(days=6)
        end = fields.Date.to_date(options.get("date_end")) if options.get("date_end") else today
        if end < start:
            raise ValidationError(_("The end date must be on or after the start date."))
        if (end - start).days > 92:
            raise ValidationError(_("Choose a date range of 93 days or fewer."))
        return start, end

    def _utc_range(self, start, end):
        timezone = pytz.timezone(self.env.user.tz or "UTC")
        start_local = timezone.localize(datetime.combine(start, time.min))
        end_local = timezone.localize(datetime.combine(end + timedelta(days=1), time.min))
        return (
            start_local.astimezone(pytz.UTC).replace(tzinfo=None),
            end_local.astimezone(pytz.UTC).replace(tzinfo=None),
        )

    @api.model
    def get_dashboard_data(self, options=None):
        self._require_admin()
        options = options or {}
        start, end = self._date_range(options)
        utc_start, utc_end = self._utc_range(start, end)

        sky = self.env["sale.order"].sudo().get_sky_dashboard_data({
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
            "config_id": int(options.get("config_id") or 0),
        })

        website_domain = [
            ("date_order", ">=", utc_start),
            ("date_order", "<", utc_end),
            "|",
            ("website_id", "!=", False),
            ("lucy_order_channel", "=", "nextjs"),
        ]
        website_orders = self.env["sale.order"].sudo().search(website_domain, order="date_order desc, id desc")
        website_days = {}
        cursor = start
        while cursor <= end:
            website_days[cursor.isoformat()] = {
                "date": cursor.isoformat(),
                "label": cursor.strftime("%a %d"),
                "orders": 0,
                "revenue": 0.0,
            }
            cursor += timedelta(days=1)
        for order in website_orders:
            local_day = fields.Datetime.context_timestamp(self, order.date_order).date().isoformat()
            if local_day in website_days:
                website_days[local_day]["orders"] += 1
                if order.state in ("sale", "done"):
                    website_days[local_day]["revenue"] += order.amount_total
        active_website_orders = website_orders.filtered(lambda order: order.state != "cancel")
        website_revenue = sum(
            active_website_orders.filtered(lambda order: order.state in ("sale", "done")).mapped("amount_total")
        )
        def is_paid(order):
            posted_invoices = order.invoice_ids.filtered(lambda invoice: invoice.state == "posted")
            return bool(posted_invoices) and all(
                invoice.payment_state in ("in_payment", "paid") for invoice in posted_invoices
            )

        website_paid = website_orders.filtered(is_paid)
        website_delivered = website_orders.filtered(
            lambda order: order.picking_ids and all(picking.state == "done" for picking in order.picking_ids)
        )
        website_processing = website_orders.filtered(
            lambda order: order.state in ("sale", "done")
            and order not in website_delivered
            and (
                not order.picking_ids
                or any(picking.state not in ("done", "cancel") for picking in order.picking_ids)
            )
        )

        website_grooming_domain = [
            ("appointment_date", ">=", utc_start),
            ("appointment_date", "<", utc_end),
            ("booking_source", "in", ("odoo_website", "nextjs", "portal")),
        ]
        website_grooming = self.env["grooming.appointment"].sudo().search(
            website_grooming_domain, order="appointment_date desc, id desc"
        )

        Product = self.env["product.product"].sudo()
        product_domain = [("active", "=", True)]
        if "is_storable" in Product._fields:
            product_domain.append(("is_storable", "=", True))
        out_of_stock = Product.search_count(product_domain + [("qty_available", "<=", 0)])
        storable_products = Product.search_count(product_domain)
        low_stock = min(int(sky.get("low_stock", 0)), storable_products)
        low_only = max(low_stock - out_of_stock, 0)
        healthy_stock = max(storable_products - low_stock, 0)
        inventory_value = 0.0
        if "stock.valuation.layer" in self.env:
            valuation = self.env["stock.valuation.layer"].sudo().read_group(
                [("company_id", "=", self.env.company.id)], ["value:sum"], []
            )
            inventory_value = valuation[0].get("value", 0.0) if valuation else 0.0

        all_period_grooming = self.env["grooming.appointment"].sudo().search([
            ("appointment_date", ">=", utc_start),
            ("appointment_date", "<", utc_end),
            ("state", "=", "completed"),
            ("appt_payment_status", "=", "paid"),
        ])
        standalone_grooming = all_period_grooming.filtered(
            lambda appointment: not appointment.pos_order_id and not appointment.sale_order_id
        )
        standalone_grooming_revenue = sum(standalone_grooming.mapped("total_price"))
        consolidated_revenue = sky["weekly"]["net_sales"] + website_revenue + standalone_grooming_revenue

        # Catalog intelligence uses the same canonical category trees consumed
        # by the Next.js storefront. It is read-only and never rewrites products.
        Category = self.env["product.category"].sudo()
        Template = self.env["product.template"].sudo()
        all_categories = Category.search([])
        roots_by_name = {
            (category.name or "").strip().upper(): category
            for category in all_categories.filtered(lambda category: not category.parent_id)
        }
        catalog_definitions = [
            ("dogs", "Dogs", "🐶", "DOGS"),
            ("cats", "Cats", "🐱", "CATS"),
            ("birds", "Birds", "🐦", "BIRDS"),
            ("small_animals", "Small Animals", "🐰", "SMALL ANIMALS"),
        ]
        catalog_groups = []
        for key, label, icon, root_name in catalog_definitions:
            root = roots_by_name.get(root_name)
            category_ids = Category.search([("id", "child_of", root.id)]).ids if root else []
            template_domain = [
                ("active", "=", True),
                ("sale_ok", "=", True),
                ("categ_id", "in", category_ids or [0]),
            ]
            templates = Template.search(template_domain)
            template_ids = templates.ids
            variants = templates.mapped("product_variant_ids")
            variant_ids = variants.ids
            pos_lines = self.env["pos.order.line"].sudo().search([
                ("order_id.date_order", ">=", utc_start),
                ("order_id.date_order", "<", utc_end),
                ("order_id.state", "in", ("paid", "done", "invoiced")),
                ("product_id", "in", variant_ids or [0]),
            ])
            website_lines = website_orders.mapped("order_line").filtered(
                lambda line: line.product_id.product_tmpl_id.id in template_ids
                and line.order_id.state in ("sale", "done")
            )
            product_sales = {}
            for line in pos_lines:
                template_id = line.product_id.product_tmpl_id.id
                values = product_sales.setdefault(template_id, {"units": 0.0, "revenue": 0.0})
                values["units"] += line.qty
                values["revenue"] += line.price_subtotal_incl
            for line in website_lines:
                template_id = line.product_id.product_tmpl_id.id
                values = product_sales.setdefault(template_id, {"units": 0.0, "revenue": 0.0})
                values["units"] += line.product_uom_qty
                values["revenue"] += line.price_total

            stock_units = sum(variants.mapped("qty_available"))
            out_count = Template.search_count(template_domain + [("qty_available", "<=", 0)])
            low_count = Template.search_count(template_domain + [
                ("qty_available", ">", 0), ("qty_available", "<=", 5)
            ])
            healthy_count = max(len(templates) - low_count - out_count, 0)
            published_field = "website_published" if "website_published" in Template._fields else "is_published"
            published_count = Template.search_count(
                template_domain + [(published_field, "=", True)]
            ) if published_field in Template._fields else 0
            with_images = Template.search_count(template_domain + [("image_128", "!=", False)])
            missing_images = len(templates) - with_images
            zero_price = Template.search_count(template_domain + [("list_price", "<=", 0)])
            missing_description = Template.search_count(template_domain + [
                ("description_sale", "=", False), ("description", "=", False)
            ])
            top_products = sorted(
                templates,
                key=lambda product: product_sales.get(product.id, {}).get("revenue", 0.0),
                reverse=True,
            )[:6]
            catalog_groups.append({
                "key": key,
                "name": label,
                "icon": icon,
                "root_category_id": root.id if root else 0,
                "category_ids": category_ids,
                "products": len(templates),
                "published": published_count,
                "with_images": with_images,
                "missing_images": missing_images,
                "zero_price": zero_price,
                "missing_description": missing_description,
                "stock_units": stock_units,
                "healthy": healthy_count,
                "low_stock": low_count,
                "out_of_stock": out_count,
                "inventory_value": sum(
                    max(product.qty_available, 0.0) * product.standard_price for product in templates
                ),
                "pos_revenue": sum(pos_lines.mapped("price_subtotal_incl")),
                "website_revenue": sum(website_lines.mapped("price_total")),
                "units_sold": sum(pos_lines.mapped("qty")) + sum(website_lines.mapped("product_uom_qty")),
                "top_products": [{
                    "id": product.id,
                    "name": product.display_name,
                    "price": product.list_price,
                    "stock": product.qty_available,
                    "units": product_sales.get(product.id, {}).get("units", 0.0),
                    "revenue": product_sales.get(product.id, {}).get("revenue", 0.0),
                    "image": f"/web/image/product.template/{product.id}/image_128",
                } for product in top_products],
            })

        return {
            "date_start": start.isoformat(),
            "date_end": end.isoformat(),
            "utc_start": fields.Datetime.to_string(utc_start),
            "utc_end": fields.Datetime.to_string(utc_end),
            "currency": self.env.company.currency_id.symbol or self.env.company.currency_id.name,
            "sky": sky,
            "overview": {
                "consolidated_revenue": consolidated_revenue,
                "standalone_grooming_revenue": standalone_grooming_revenue,
                "channels": [
                    {"name": "Point of Sale", "value": sky["weekly"]["net_sales"], "color": "#4e2a15"},
                    {"name": "Website", "value": website_revenue, "color": "#c77e35"},
                    {"name": "Grooming", "value": standalone_grooming_revenue, "color": "#8da17e"},
                ],
            },
            "website": {
                "orders": len(website_orders),
                "revenue": website_revenue,
                "average_order": website_revenue / len(active_website_orders) if active_website_orders else 0.0,
                "draft": len(website_orders.filtered(lambda order: order.state in ("draft", "sent"))),
                "confirmed": len(website_orders.filtered(lambda order: order.state in ("sale", "done"))),
                "payment_pending": len(website_orders.filtered(
                    lambda order: order.state in ("sale", "done") and order not in website_paid
                )),
                "paid": len(website_paid),
                "processing": len(website_processing),
                "delivered": len(website_delivered),
                "cancelled": len(website_orders.filtered(lambda order: order.state == "cancel")),
                "days": list(website_days.values()),
                "recent": [{
                    "id": order.id,
                    "name": order.name,
                    "customer": order.partner_id.display_name,
                    "date": fields.Datetime.context_timestamp(self, order.date_order).strftime("%d %b %Y, %H:%M"),
                    "state": order.state,
                    "amount": order.amount_total,
                } for order in website_orders[:6]],
            },
            "grooming": {
                "website_bookings": len(website_grooming),
                "pending": len(website_grooming.filtered(lambda appointment: appointment.state == "pending")),
                "confirmed": len(website_grooming.filtered(lambda appointment: appointment.state == "confirmed")),
                "in_progress": len(website_grooming.filtered(
                    lambda appointment: appointment.state in ("checked_in", "in_progress", "halfway")
                )),
                "completed": len(website_grooming.filtered(lambda appointment: appointment.state == "completed")),
                "cancelled": len(website_grooming.filtered(lambda appointment: appointment.state == "cancelled")),
                "recent": [{
                    "id": appointment.id,
                    "reference": appointment.name,
                    "customer": appointment.partner_id.display_name,
                    "pet": appointment.pet_name,
                    "date": fields.Datetime.context_timestamp(self, appointment.appointment_date).strftime("%d %b %Y, %H:%M"),
                    "state": appointment.state,
                } for appointment in website_grooming[:6]],
            },
            "inventory": {
                "active_products": sky.get("products", 0),
                "low_stock": sky.get("low_stock", 0),
                "out_of_stock": out_of_stock,
                "inventory_value": inventory_value,
                "pending_replenishments": sky.get("pending_replenishments", 0),
                "storable_products": storable_products,
                "healthy_stock": healthy_stock,
                "low_only": low_only,
            },
            "catalog": catalog_groups,
        }
