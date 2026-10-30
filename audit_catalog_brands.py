import collections
import json
import re
import xmlrpc.client


URL = "https://erp.stephanspetstore.co.tz"
DB = "Stephans"
USERNAME = "info@stephanspetstore.co.tz"
PASSWORD = "Stephan@3202"

common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common", allow_none=True)
uid = common.authenticate(DB, USERNAME, PASSWORD, {})
if not uid:
    raise SystemExit("Authentication failed")
models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)


def call(model, method, args=None, kwargs=None):
    return models.execute_kw(DB, uid, PASSWORD, model, method, args or [], kwargs or {})


product_fields = call(
    "product.template", "fields_get", [],
    {"attributes": ["type", "relation", "string"]},
)
brand_candidates = {
    name: spec for name, spec in product_fields.items()
    if "brand" in name.casefold() or "brand" in (spec.get("string") or "").casefold()
}
brand_field = next(
    (name for name in ("brand_id", "product_brand_id", "x_brand_id") if name in brand_candidates),
    None,
)
if not brand_field:
    print(json.dumps({"error": "No product brand field found", "brand_candidates": brand_candidates}, indent=2))
    raise SystemExit(1)
brand_model = brand_candidates[brand_field].get("relation")

brand_fields = call(brand_model, "fields_get", [], {"attributes": ["type"]})
fields = [f for f in ("name", "active", "logo", "website_url") if f in brand_fields]
brands = call(
    brand_model, "search_read", [[]],
    {"fields": fields, "order": "name", "context": {"active_test": False}},
)

read_fields = [f for f in ("name", "active", "sale_ok", brand_field, "image_128") if f in product_fields]
products = call(
    "product.template", "search_read", [[]],
    {"fields": read_fields, "context": {"active_test": False}},
)
shop = [p for p in products if p.get("active") and p.get("sale_ok")]


def normalize(value):
    return re.sub(r"[^a-z0-9]+", "", (value or "").casefold())


name_groups = collections.defaultdict(list)
for brand in brands:
    name_groups[normalize(brand["name"])].append({"id": brand["id"], "name": brand["name"]})

usage = collections.Counter(p[brand_field][0] for p in shop if p.get(brand_field))
brand_rows = []
for brand in brands:
    logo = brand.get("logo")
    brand_rows.append({
        "id": brand["id"],
        "name": brand["name"],
        "active": brand.get("active", True),
        "shop_products": usage[brand["id"]],
        "has_logo": bool(logo),
        "website_url": brand.get("website_url") or None,
    })

brand_names = [(b["id"], b["name"], normalize(b["name"])) for b in brands if len(normalize(b["name"])) >= 4]
unassigned = [p for p in shop if not p.get(brand_field)]
likely_missing = []
for product in unassigned:
    normalized_product = normalize(product["name"])
    matches = [{"id": bid, "name": name} for bid, name, token in brand_names if token in normalized_product]
    if matches:
        likely_missing.append({"id": product["id"], "name": product["name"], "matching_brands": matches})

assigned_name_conflicts = []
brand_by_id = {b["id"]: b for b in brands}
for product in shop:
    if not product.get(brand_field):
        continue
    assigned = brand_by_id.get(product[brand_field][0])
    if not assigned:
        assigned_name_conflicts.append({"id": product["id"], "name": product["name"], "brand": product[brand_field]})

report = {
    "counts": {
        "brand_field": brand_field,
        "brand_model": brand_model,
        "brands": len(brands),
        "active_sale_products": len(shop),
        "products_with_brand": len(shop) - len(unassigned),
        "products_without_brand": len(unassigned),
        "unassigned_products_whose_name_matches_a_brand": len(likely_missing),
        "duplicate_normalized_brand_groups": sum(len(rows) > 1 for rows in name_groups.values()),
        "brands_without_shop_products": sum(row["shop_products"] == 0 for row in brand_rows),
        "brands_without_logo": sum(not row["has_logo"] for row in brand_rows),
        "active_products_without_image": sum(not p.get("image_128") for p in shop),
    },
    "brands": brand_rows,
    "duplicate_brands": [rows for rows in name_groups.values() if len(rows) > 1],
    "likely_missing_brand_assignments": likely_missing,
    "invalid_brand_references": assigned_name_conflicts,
}
print(json.dumps(report, indent=2))
