import logging

from odoo import http
from odoo.http import request


_logger = logging.getLogger(__name__)


class StephansWebsiteHome(http.Controller):
    FEATURED_SLIDE = [
        {
            "id": "featured-parrot",
            "name": "Plush Parrot Dog Toy",
            "category": "Pet Toys",
            "price_formatted": "Tsh 28,000",
            "url": "/shop?search=Plush+Parrot+Dog+Toy",
            "image_url": "/stephans_website_theme/static/src/images/products/plush-parrot-dog-toy.webp",
        },
        {
            "id": "featured-fountain",
            "name": "Cat Water Fountain Bubble Boy",
            "category": "Cat Accessories",
            "price_formatted": "Tsh 140,000",
            "url": "/shop?search=Cat+Water+Fountain+Bubble+Boy",
            "image_url": "/stephans_website_theme/static/src/images/products/cat-water-fountain.webp",
        },
        {
            "id": "featured-rabbit",
            "name": "Rabbit House C",
            "category": "Pets",
            "price_formatted": "Tsh 55,000",
            "url": "/shop?search=Rabbit+House+C",
            "image_url": "/stephans_website_theme/static/src/images/products/rabbit-house-c.webp",
        },
        {
            "id": "featured-cage",
            "name": "Flying Bird Cage Medium",
            "category": "Pets",
            "price_formatted": "Tsh 85,000",
            "url": "/shop?search=Flying+Bird+Cage+Medium",
            "image_url": "/stephans_website_theme/static/src/images/products/flying-bird-cage.webp",
        },
    ]

    @staticmethod
    def _normalise_name(value):
        return " ".join((value or "").lower().split())

    def _format_product(self, product):
        category = product.public_categ_ids[:1].name or "Pet Essentials"
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
        """Return one fixed featured slide followed by live four-product sets.

        Live records must be active, saleable, website-published, priced and have
        a product image. Pet buckets improve variety; a global fallback ensures a
        thin category never prevents complete four-card slides.
        """
        slides = [list(self.FEATURED_SLIDE)]
        if max_slides <= 1:
            return slides

        if env is None:
            try:
                env = request.env
            except Exception:
                return slides

        try:
            ProductTemplate = env["product.template"].sudo()
            candidates = list(ProductTemplate.search([
                ("active", "=", True),
                ("sale_ok", "=", True),
                ("website_published", "=", True),
                ("list_price", ">", 0),
                ("image_1920", "!=", False),
            ], order="create_date desc, id desc", limit=max(64, max_slides * 20)))

            featured_names = {
                self._normalise_name(product["name"])
                for product in self.FEATURED_SLIDE
            }
            candidates = [
                product for product in candidates
                if self._normalise_name(product.name) not in featured_names
            ]

            buckets = {"dog": [], "cat": [], "small": [], "bird": [], "other": []}
            for product in candidates:
                category_text = " ".join(product.public_categ_ids.mapped("name")).lower()
                if any(word in category_text for word in ("dog", "puppy", "canine")):
                    bucket = "dog"
                elif any(word in category_text for word in ("cat", "kitten", "feline")):
                    bucket = "cat"
                elif any(word in category_text for word in ("bird", "avian")):
                    bucket = "bird"
                elif any(word in category_text for word in ("small animal", "rabbit", "hamster", "guinea")):
                    bucket = "small"
                else:
                    bucket = "other"
                buckets[bucket].append(product)

            used_ids = set()
            bucket_order = ("dog", "cat", "small", "bird")
            for _slide_number in range(max_slides - 1):
                selected = []

                # Prefer one product per pet family for a balanced row.
                for bucket_name in bucket_order:
                    product = next(
                        (item for item in buckets[bucket_name] if item.id not in used_ids),
                        None,
                    )
                    if product:
                        selected.append(product)
                        used_ids.add(product.id)

                # Fill gaps from the newest remaining live catalog products.
                for product in candidates:
                    if len(selected) == 4:
                        break
                    if product.id not in used_ids:
                        selected.append(product)
                        used_ids.add(product.id)

                if len(selected) != 4:
                    break
                slides.append([self._format_product(product) for product in selected])

            return slides
        except Exception:
            _logger.exception("Could not build Stephan's live new-arrival slides")
            return slides

    @http.route("/", type="http", auth="public", website=True, sitemap=True)
    def homepage(self, **kwargs):
        return request.render("stephans_website_theme.stephans_preview_page", {
            "product_slides": self._get_balanced_product_slides(max_slides=4),
        })

    @http.route("/stephans/api/new-arrivals", type="jsonrpc", auth="public", website=True)
    def api_new_arrivals(self, **kwargs):
        slides = self._get_balanced_product_slides(max_slides=4)
        return {"status": "success", "slides": slides, "rotation_ms": 20000}
