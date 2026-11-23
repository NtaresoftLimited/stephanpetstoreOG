from collections import defaultdict
from datetime import datetime, timedelta
import logging

from odoo import http
from odoo.http import request
from ..models.shared_cache import (
    get_cached,
    set_cached,
    TTL_HOMEPAGE_SECONDS,
)

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
            # Serve 480-512px card derivative instead of heavy image_1024
            "image_url": "/web/image/product.template/{}/image_512?unique={}".format(product.id, cache_key),
        }

    def _get_balanced_product_slides(self, env=None, max_slides=4, force_refresh=False):
        """Return best seller products from last month and this week (strictly In-Stock Only).

        Groups products into 4-product slides for the homepage carousel.
        Uses cross-worker shared RAM cache (/dev/shm) and direct SQL aggregation (< 5ms).
        """
        if env is None:
            try:
                env = request.env
            except Exception:
                env = None

        cache_key = f"best_sellers_slides_{max_slides}"
        if not force_refresh:
            cached_slides = get_cached("homepage_groups", cache_key, env=env)
            if cached_slides:
                return cached_slides

        if env is None:
            return []

        try:
            now = datetime.now()
            first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            last_month_start = (first_of_this_month - timedelta(days=1)).replace(day=1)
            target_count = max_slides * 4

            # Single-pass SQL query:
            # 1. Aggregates POS + eCommerce sales quantities
            # 2. Aggregates on-hand internal stock quantities (qty_available > 0)
            # 3. Verifies presence of product image attachment (image_1920 / image_512 / image_128)
            # 4. Filters active, published, sale_ok, list_price > 0 products
            fast_best_sellers_sql = """
                WITH sales_agg AS (
                    SELECT tmpl_id, SUM(qty) AS total_sold FROM (
                        SELECT pp.product_tmpl_id AS tmpl_id, pol.qty AS qty
                        FROM pos_order_line pol
                        JOIN pos_order po ON po.id = pol.order_id
                        JOIN product_product pp ON pp.id = pol.product_id
                        WHERE po.date_order >= %s
                          AND po.state IN ('paid', 'done', 'invoiced')
                        UNION ALL
                        SELECT pp.product_tmpl_id AS tmpl_id, sol.product_uom_qty AS qty
                        FROM sale_order_line sol
                        JOIN sale_order so ON so.id = sol.order_id
                        JOIN product_product pp ON pp.id = sol.product_id
                        WHERE so.date_order >= %s
                          AND so.state IN ('sale', 'done')
                    ) s
                    GROUP BY tmpl_id
                ),
                stock_agg AS (
                    SELECT pp.product_tmpl_id AS tmpl_id, SUM(sq.quantity) AS qty_on_hand
                    FROM stock_quant sq
                    JOIN stock_location sl ON sl.id = sq.location_id
                    JOIN product_product pp ON pp.id = sq.product_id
                    WHERE sl.usage = 'internal'
                    GROUP BY pp.product_tmpl_id
                    HAVING SUM(sq.quantity) > 0
                ),
                img_check AS (
                    SELECT DISTINCT res_id AS tmpl_id
                    FROM ir_attachment
                    WHERE res_model = 'product.template'
                      AND res_field IN ('image_1920', 'image_1024', 'image_512', 'image_128')
                )
                SELECT pt.id
                FROM product_template pt
                JOIN stock_agg st ON st.tmpl_id = pt.id
                JOIN img_check im ON im.tmpl_id = pt.id
                LEFT JOIN sales_agg sa ON sa.tmpl_id = pt.id
                WHERE pt.active = TRUE
                  AND pt.sale_ok = TRUE
                  AND pt.is_published = TRUE
                  AND pt.list_price > 0
                  AND COALESCE(pt.type, 'consu') != 'service'
                ORDER BY COALESCE(sa.total_sold, 0) DESC, st.qty_on_hand DESC, pt.id DESC
                LIMIT %s;
            """
            env.cr.execute(fast_best_sellers_sql, (last_month_start, last_month_start, target_count))
            top_ids = [row[0] for row in env.cr.fetchall()]

            ProductTemplate = env["product.template"].sudo()
            selected = list(ProductTemplate.browse(top_ids))

            slides = []
            for i in range(0, len(selected), 4):
                chunk = selected[i:i + 4]
                if len(chunk) == 4:
                    slides.append([self._format_product(p) for p in chunk])

            if slides:
                set_cached(
                    "homepage_groups",
                    cache_key,
                    slides,
                    ttl=TTL_HOMEPAGE_SECONDS,
                    product_ids=top_ids,
                    env=env,
                )

            return slides
        except Exception:
            _logger.exception("Could not build Stephan's live best-seller slides")
            return []

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
