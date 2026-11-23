from collections import defaultdict
from datetime import datetime, timedelta
import logging
import time

from odoo import http
from odoo.http import request


_logger = logging.getLogger(__name__)

# Module-level thread-safe cache for homepage product rotator slides:
# - TTL: 600s (10 minutes)
# - Eliminates heavy stock & multi-table sales re-computation on every page hit
_SLIDES_CACHE = {
    "timestamp": 0,
    "slides": [],
}
_CACHE_TTL = 600


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

    def _get_balanced_product_slides(self, env=None, max_slides=4, force_refresh=False):
        """Return best seller products from last month and this week (strictly In-Stock Only).

        Groups products into 4-product slides for the homepage carousel.
        Includes high-performance in-memory caching and optimized direct SQL sales aggregation.
        """
        now_ts = time.time()
        if not force_refresh and _SLIDES_CACHE["slides"] and (now_ts - _SLIDES_CACHE["timestamp"] < _CACHE_TTL):
            return _SLIDES_CACHE["slides"]

        if env is None:
            try:
                env = request.env
            except Exception:
                return _SLIDES_CACHE.get("slides", [])

        try:
            now = datetime.now()
            first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_start = (first_of_this_month - timedelta(days=1)).replace(day=1)

            total_sold = defaultdict(float)

            # 1. Fast SQL Aggregation: Combines POS + Sale Orders in ONE single query
            try:
                sales_sql = """
                    SELECT tmpl_id, SUM(qty) AS total_qty FROM (
                        SELECT pt.id AS tmpl_id, pol.qty AS qty
                        FROM pos_order_line pol
                        JOIN pos_order po ON po.id = pol.order_id
                        JOIN product_product pp ON pp.id = pol.product_id
                        JOIN product_template pt ON pt.id = pp.product_tmpl_id
                        WHERE po.date_order >= %s
                          AND po.state IN ('paid', 'done', 'invoiced')
                          AND pt.type != 'service'
                        UNION ALL
                        SELECT pt.id AS tmpl_id, sol.product_uom_qty AS qty
                        FROM sale_order_line sol
                        JOIN sale_order so ON so.id = sol.order_id
                        JOIN product_product pp ON pp.id = sol.product_id
                        JOIN product_template pt ON pt.id = pp.product_tmpl_id
                        WHERE so.date_order >= %s
                          AND so.state IN ('sale', 'done')
                          AND pt.type != 'service'
                    ) combined
                    GROUP BY tmpl_id;
                """
                env.cr.execute(sales_sql, (last_month_start, last_month_start))
                for row in env.cr.fetchall():
                    total_sold[row[0]] = float(row[1] or 0.0)
            except Exception as sql_err:
                _logger.warning("Direct SQL sales count failed, falling back to ORM: %s", sql_err)
                # Fallback to ORM if SQL table schema differs
                pos_lines = env["pos.order.line"].sudo().search([
                    ("order_id.date_order", ">=", last_month_start),
                    ("order_id.state", "in", ["paid", "done", "invoiced"]),
                    ("product_id.type", "!=", "service"),
                ])
                for line in pos_lines:
                    if line.product_id and line.product_id.product_tmpl_id:
                        total_sold[line.product_id.product_tmpl_id.id] += line.qty

                so_lines = env["sale.order.line"].sudo().search([
                    ("order_id.date_order", ">=", last_month_start),
                    ("order_id.state", "in", ["sale", "done"]),
                    ("product_id.type", "!=", "service"),
                ])
                for line in so_lines:
                    if line.product_id and line.product_id.product_tmpl_id:
                        total_sold[line.product_id.product_tmpl_id.id] += line.product_uom_qty

            # 2. Eligible in-stock published products
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

            # 3. Rank candidates by (quantity sold desc, qty_available desc, id desc)
            ranked = sorted(
                candidates,
                key=lambda p: (total_sold.get(p.id, 0.0), p.qty_available, p.id),
                reverse=True,
            )

            # 4. Chunk into 4-product slides
            slides = []
            target_count = max_slides * 4
            selected = ranked[:target_count]

            for i in range(0, len(selected), 4):
                chunk = selected[i:i + 4]
                if len(chunk) == 4:
                    slides.append([self._format_product(p) for p in chunk])

            # Update cache if valid slides were constructed
            if slides:
                _SLIDES_CACHE["timestamp"] = now_ts
                _SLIDES_CACHE["slides"] = slides

            return slides or _SLIDES_CACHE.get("slides", [])
        except Exception:
            _logger.exception("Could not build Stephan's live best-seller slides")
            return _SLIDES_CACHE.get("slides", [])

    @http.route("/", type="http", auth="public", website=True, sitemap=True)
    def homepage(self, **kwargs):
        if request.httprequest.host.split(':')[0] == 'stephanspetstore.co.tz':
            return request.redirect('https://www.stephanspetstore.co.tz/', code=301, local=False)
        force_refresh = bool(kwargs.get('refresh_cache') or kwargs.get('nocache'))
        return request.render("stephans_website_theme.stephans_preview_page", {
            "product_slides": self._get_balanced_product_slides(max_slides=4, force_refresh=force_refresh),
            "additional_title": "Premium Pet Store & Grooming in Tanzania",
            "meta_description": "Shop premium pet food, accessories and toys, or book professional pet grooming at Stephan's Pet Store in Masaki and Mikocheni, Dar es Salaam.",
        })

    @http.route("/stephans/api/new-arrivals", type="jsonrpc", auth="public", website=True)
    def api_new_arrivals(self, **kwargs):
        force_refresh = bool(kwargs.get('force_refresh'))
        slides = self._get_balanced_product_slides(max_slides=4, force_refresh=force_refresh)
        return {"status": "success", "slides": slides, "rotation_ms": 15000}
