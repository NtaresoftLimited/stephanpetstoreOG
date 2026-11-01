from odoo import http
from odoo.http import request


class StephansWebsiteHome(http.Controller):
    def _get_balanced_product_slides(self, env=None, max_slides=4):
        """Dynamic filter for New Arrivals:
        Balances 1 Dog, 1 Cat, 1 Small Animal, 1 Bird per slide (strictly 4 products per slide).
        """
        if env is None:
            try:
                env = request.env
            except Exception:
                return []

        try:
            PublicCategory = env["product.public.category"].sudo()
            ProductTemplate = env["product.template"].sudo()

            def get_subcat_ids(root_names):
                cats = PublicCategory.search([("name", "in", root_names)])
                all_ids = []
                for c in cats:
                    all_ids.extend(PublicCategory.search([("id", "child_of", c.id)]).ids)
                return list(set(all_ids))

            dog_cats = get_subcat_ids(["Dogs", "Dog"])
            cat_cats = get_subcat_ids(["Cats", "Cat", "Cat Accessories"])
            bird_cats = get_subcat_ids(["Birds", "Bird"])
            small_cats = get_subcat_ids(["Small Animals", "Small Animal", "Pets"])

            domain_base = [
                ("website_published", "=", True),
                ("image_1920", "!=", False),
            ]

            dogs = list(ProductTemplate.search(domain_base + [("public_categ_ids", "in", dog_cats)], order="create_date desc", limit=16))
            cats = list(ProductTemplate.search(domain_base + [("public_categ_ids", "in", cat_cats)], order="create_date desc", limit=16))
            birds = list(ProductTemplate.search(domain_base + [("public_categ_ids", "in", bird_cats)], order="create_date desc", limit=16))
            smalls = list(ProductTemplate.search(domain_base + [("public_categ_ids", "in", small_cats)], order="create_date desc", limit=16))

            def format_prod(p, default_cat):
                cat_name = p.public_categ_ids[0].name if p.public_categ_ids else default_cat
                price_val = f"Tsh {int(p.list_price):,}" if p.list_price else "Tsh 0"
                return {
                    "id": p.id,
                    "name": p.name or "",
                    "category": cat_name or default_cat,
                    "price_formatted": price_val,
                    "url": f"/shop/{p.id}",
                    "image_url": f"/web/image/product.template/{p.id}/image_512",
                }

            slides = []

            # Slide 1: Featured New Arrivals (matches Stephan's Pet Store brand hero products)
            slide_1 = [
                {
                    "id": "parrot",
                    "name": "Plush Parrot Dog Toy",
                    "category": "Pet Toys",
                    "price_formatted": "Tsh 28,000",
                    "url": "/shop?search=Plush+Parrot+Dog+Toy",
                    "image_url": "/stephans_website_theme/static/src/images/products/plush-parrot-dog-toy.webp",
                },
                {
                    "id": "fountain",
                    "name": "Cat Water Fountain Bubble Boy",
                    "category": "Cat Accessories",
                    "price_formatted": "Tsh 140,000",
                    "url": "/shop?search=Cat+Water+Fountain+Bubble+Boy",
                    "image_url": "/stephans_website_theme/static/src/images/products/cat-water-fountain.webp",
                },
                {
                    "id": "rabbit",
                    "name": "Rabbit House C",
                    "category": "Pets",
                    "price_formatted": "Tsh 55,000",
                    "url": "/shop?search=Rabbit+House+C",
                    "image_url": "/stephans_website_theme/static/src/images/products/rabbit-house-c.webp",
                },
                {
                    "id": "cage",
                    "name": "Flying Bird Cage Medium",
                    "category": "Pets",
                    "price_formatted": "Tsh 85,000",
                    "url": "/shop?search=Flying+Bird+Cage+Medium",
                    "image_url": "/stephans_website_theme/static/src/images/products/flying-bird-cage.webp",
                },
            ]
            slides.append(slide_1)

            # Subsequent slides dynamically generated from database: 1 Dog, 1 Cat, 1 Small Animal, 1 Bird
            max_dynamic = min(len(dogs), len(cats), len(smalls), len(birds), max_slides - 1)
            for i in range(max_dynamic):
                slide = [
                    format_prod(dogs[i], "Dogs"),
                    format_prod(cats[i], "Cats"),
                    format_prod(smalls[i], "Small Animals"),
                    format_prod(birds[i], "Birds"),
                ]
                # Ensure strictly 4 products per slide
                if len(slide) == 4:
                    slides.append(slide)

            return slides
        except Exception:
            return []

    @http.route("/", type="http", auth="public", website=True, sitemap=True)
    def homepage(self, **kwargs):
        slides = self._get_balanced_product_slides(max_slides=4)
        return request.render("stephans_website_theme.stephans_preview_page", {
            "product_slides": slides,
        })

    @http.route("/stephans/api/new-arrivals", type="jsonrpc", auth="public", website=True)
    def api_new_arrivals(self, **kwargs):
        slides = self._get_balanced_product_slides(max_slides=4)
        return {"status": "success", "slides": slides}
