from collections import defaultdict
from datetime import datetime, timedelta
import logging

from odoo import http
from odoo.http import request


_logger = logging.getLogger(__name__)


class StephansWebsiteHome(http.Controller):

    def _format_product(self, product):
        category = product.public_categ_ids[:1].name or (
            product.categ_id.name if product.categ_id and product.categ_id.name != "All" else "Pet Essentials"
        )
        cache_key = product.write_date.strftime("%Y%m%d%H%M%S") if product.write_date else product.id
        return {
            "id": product.id,
            "name": product.name or "",
            "category": category,
            "price_formatted": "Tsh {:,.0f}".format(product.list_price),
            "url": product.website_url or "/shop/{}".format(product.id),
            "image_url": "/web/image/product.template/{}/image_1024?unique={}".format(product.id, cache_key),
        }

    def _get_balanced_product_slides(self, env=None, max_slides=4):
        """Return best seller products from last month and this week (strictly In-Stock Only).

        Groups products into 4-product slides for the homepage carousel.
        Products must be:
        - active = True, sale_ok = True, website_published = True
        - list_price > 0
        - qty_available > 0 (In-Stock Only)
        - has image
        - sorted by total sales quantity in POS & sales orders from start of last month up to today.
        """
        if env is None:
            try:
                env = request.env
            except Exception:
                return []

        try:
            now = datetime.now()
            first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_start = (first_of_this_month - timedelta(days=1)).replace(day=1)

            total_sold = defaultdict(float)

            # 1. POS order lines
            pos_lines = env["pos.order.line"].sudo().search([
                ("order_id.date_order", ">=", last_month_start),
                ("order_id.state", "in", ["paid", "done", "invoiced"]),
                ("product_id.type", "!=", "service"),
            ])
            for line in pos_lines:
                if line.product_id and line.product_id.product_tmpl_id:
                    total_sold[line.product_id.product_tmpl_id.id] += line.qty

            # 2. Sale order lines (web shop / direct sales)
            so_lines = env["sale.order.line"].sudo().search([
                ("order_id.date_order", ">=", last_month_start),
                ("order_id.state", "in", ["sale", "done"]),
                ("product_id.type", "!=", "service"),
            ])
            for line in so_lines:
                if line.product_id and line.product_id.product_tmpl_id:
                    total_sold[line.product_id.product_tmpl_id.id] += line.product_uom_qty

            # 3. Eligible in-stock published products
            ProductTemplate = env["product.template"].sudo()
            domain = [
                ("active", "=", True),
                ("sale_ok", "=", True),
                ("website_published", "=", True),
                ("list_price", ">", 0),
                ("qty_available", ">", 0),
                "|", ("image_1920", "!=", False), ("image_128", "!=", False),
            ]
            candidates = list(ProductTemplate.search(domain))

            # 4. Rank candidates by (quantity sold desc, qty_available desc, id desc)
            ranked = sorted(
                candidates,
                key=lambda p: (total_sold.get(p.id, 0.0), p.qty_available, p.id),
                reverse=True,
            )

            # 5. Chunk into 4-product slides
            slides = []
            target_count = max_slides * 4
            selected = ranked[:target_count]

            for i in range(0, len(selected), 4):
                chunk = selected[i:i + 4]
                if len(chunk) == 4:
                    slides.append([self._format_product(p) for p in chunk])

            return slides
        except Exception:
            _logger.exception("Could not build Stephan's live best-seller slides")
            return []

    @http.route("/", type="http", auth="public", website=True, sitemap=True)
    def homepage(self, **kwargs):
        return request.render("stephans_website_theme.stephans_preview_page", {
            "product_slides": self._get_balanced_product_slides(max_slides=4),
            "additional_title": "Premium Pet Store & Grooming in Tanzania",
            "meta_description": "Shop premium pet food, accessories and toys, or book professional pet grooming at Stephan's Pet Store in Masaki and Mikocheni, Dar es Salaam.",
        })

    @http.route("/stephans/api/new-arrivals", type="jsonrpc", auth="public", website=True)
    def api_new_arrivals(self, **kwargs):
        slides = self._get_balanced_product_slides(max_slides=4)
        return {"status": "success", "slides": slides, "rotation_ms": 20000}
