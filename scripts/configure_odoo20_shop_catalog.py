"""Prepare the imported Odoo 20 catalogue for safe public browsing.

Run inside the Odoo 20 shell after the Odoo 18 product migration. The script
never invents prices: imported products with placeholder prices are unpublished
until an administrator supplies a valid retail price.
"""

import json
import re


MIGRATION_MODULE = "stephans_product_migration"


def normalized(value):
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def category(name, parent=False):
    domain = [("name", "=", name), ("parent_id", "=", parent.id if parent else False)]
    record = env["product.public.category"].sudo().search(domain, limit=1)
    if not record:
        record = env["product.public.category"].sudo().create({
            "name": name,
            "parent_id": parent.id if parent else False,
        })
    return record


def contains_any(text, words):
    return any(word in text for word in words)


model_data = env["ir.model.data"].sudo().search([
    ("module", "=", MIGRATION_MODULE),
    ("model", "=", "product.template"),
])
products = env["product.template"].sudo().with_context(active_test=False).browse(
    list(set(model_data.mapped("res_id")))
).exists()

roots = {
    "Dogs": category("Dogs"),
    "Cats": category("Cats"),
    "Birds": category("Birds"),
    "Small Animals": category("Small Animals"),
}

animal_rules = {
    "Dogs": (" dog ", " puppy ", " canine ", " kennel ", " tropidog "),
    "Cats": (" cat ", " kitten ", " feline ", " whiskas ", " litter "),
    "Birds": (" bird ", " parrot ", " budgie ", " canary ", " avian "),
    "Small Animals": (" rabbit ", " hamster ", " guinea pig ", " rodent ", " small animal "),
}

department_rules = {
    "Food": (" food ", " feed ", " kibble ", " pate ", " gravy ", " flakes "),
    "Treats": (" treat ", " biscuit ", " snack ", " bone ", " chew "),
    "Toys": (" toy ", " ball ", " plush ", " rope ", " fetch "),
    "Bowls & Feeders": (" bowl ", " feeder ", " fountain "),
    "Beds & Comfort": (" bed ", " blanket ", " mat ", " cushion "),
    "Collars, Harnesses & Leads": (" collar ", " harness ", " leash ", " lead "),
    "Grooming Essentials": (" shampoo ", " brush ", " comb ", " grooming ", " nail ", " wipe "),
    "Health & Wellness": (" flea ", " tick ", " deworm ", " vitamin ", " supplement ", " dental "),
    "Homes & Crates": (" house ", " cage ", " crate ", " carrier ", " habitat "),
    "Litter & Clean Living": (" litter ", " potty ", " poop bag ", " deodor "),
}

children = {
    root_name: {
        department_name: category(department_name, root)
        for department_name in department_rules
    }
    for root_name, root in roots.items()
}

assigned = 0
for product in products:
    text = " " + normalized(" ".join([
        product.name or "",
        product.default_code or "",
        product.categ_id.complete_name or "",
        product.description_sale or "",
    ])) + " "
    matched_roots = [name for name, words in animal_rules.items() if contains_any(text, words)]
    category_ids = set(product.public_categ_ids.ids)
    for root_name in matched_roots:
        category_ids.add(roots[root_name].id)
        for department_name, words in department_rules.items():
            if contains_any(text, words):
                category_ids.add(children[root_name][department_name].id)
    if matched_roots:
        product.public_categ_ids = [(6, 0, sorted(category_ids))]
        assigned += 1

published_field = "website_published" if "website_published" in products._fields else "is_published"
placeholder_price_products = products.filtered(lambda product: (product.list_price or 0.0) <= 1.0)
published_placeholders = placeholder_price_products.filtered(lambda product: bool(product[published_field]))
if published_placeholders:
    published_placeholders.write({published_field: False})

website = env["website"].sudo().search([], limit=1)
if website:
    website_vals = {}
    if "shop_ppg" in website._fields:
        website_vals["shop_ppg"] = 8
    if "shop_ppr" in website._fields:
        website_vals["shop_ppr"] = 4
    if website_vals:
        website.sudo().write(website_vals)

enabled_views = []
for xmlid in ("website_sale.products_categories", "website_sale.filter_products_price"):
    view = website.viewref(xmlid) if website else env.ref(xmlid, raise_if_not_found=False)
    if view and not view.active:
        view.active = True
    if view:
        enabled_views.append(xmlid)

env.cr.commit()
print("SHOP_CATALOG_CONFIGURED", json.dumps({
    "imported_products": len(products),
    "categorized_products": assigned,
    "placeholder_price_products": len(placeholder_price_products),
    "newly_unpublished_placeholders": len(published_placeholders),
    "enabled_views": enabled_views,
}, sort_keys=True))
