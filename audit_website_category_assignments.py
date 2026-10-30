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


category_fields = call("product.category", "fields_get", [], {"attributes": ["type"]})
cat_fields = [f for f in ("name", "complete_name", "parent_id", "child_id") if f in category_fields]
categories = call("product.category", "search_read", [[]], {"fields": cat_fields, "order": "id"})
cats = {row["id"]: row for row in categories}

product_fields = call("product.template", "fields_get", [], {"attributes": ["type"]})
read_fields = [
    f
    for f in (
        "name", "default_code", "active", "sale_ok", "is_published", "website_id",
        "categ_id", "x_website_category_ids", "public_categ_ids",
    )
    if f in product_fields
]
products = call(
    "product.template", "search_read", [[]],
    {"fields": read_fields, "order": "id", "context": {"active_test": False}},
)


def product_row(p):
    internal = p.get("categ_id")
    return {
        "id": p["id"],
        "name": p["name"],
        "active": p.get("active"),
        "sale_ok": p.get("sale_ok"),
        "published": p.get("is_published"),
        "internal": internal[1] if internal else None,
        "internal_id": internal[0] if internal else None,
        "website_ids": p.get("x_website_category_ids") or [],
        "website_categories": [cats[i].get("complete_name") or cats[i]["name"] for i in p.get("x_website_category_ids") or [] if i in cats],
    }


scope = [p for p in products if p.get("active") and p.get("sale_ok")]
published = [p for p in scope if p.get("is_published")]
missing = [product_row(p) for p in scope if not p.get("x_website_category_ids")]
multi = [product_row(p) for p in scope if len(p.get("x_website_category_ids") or []) > 1]
mismatch = [
    product_row(p) for p in scope
    if p.get("x_website_category_ids") and p["categ_id"][0] not in p["x_website_category_ids"]
]

by_name = collections.defaultdict(list)
for p in scope:
    normalized = re.sub(r"[^a-z0-9]+", " ", p["name"].casefold()).strip()
    by_name[normalized].append(product_row(p))
duplicate_products = [rows for rows in by_name.values() if len(rows) > 1]

placeholder_tokens = re.compile(r"\b(placeholder|test|sample|demo|dummy|temp|temporary|draft|untitled)\b", re.I)
placeholder_products = [product_row(p) for p in scope if placeholder_tokens.search(p["name"])]

path_groups = collections.defaultdict(list)
name_groups = collections.defaultdict(list)
for c in categories:
    path = c.get("complete_name") or c["name"]
    normalized_path = re.sub(r"\s*/\s*", "/", path.casefold()).strip()
    normalized_name = re.sub(r"[^a-z0-9]+", " ", c["name"].casefold()).strip()
    path_groups[normalized_path].append({"id": c["id"], "path": path})
    name_groups[normalized_name].append({"id": c["id"], "path": path})
duplicate_paths = [rows for rows in path_groups.values() if len(rows) > 1]
duplicate_names = [rows for rows in name_groups.values() if len(rows) > 1]

usage_internal = collections.Counter(p["categ_id"][0] for p in scope if p.get("categ_id"))
usage_website = collections.Counter(i for p in scope for i in p.get("x_website_category_ids") or [])
root_categories = []
for c in categories:
    if not c.get("parent_id"):
        root_categories.append({
            "id": c["id"],
            "path": c.get("complete_name") or c["name"],
            "children": len(c.get("child_id") or []),
            "internal_products": usage_internal[c["id"]],
            "website_products": usage_website[c["id"]],
        })

suspicious_ids = {
    c["id"] for c in categories
    if (c["id"] < 1102 and c["id"] not in {3, 6})
    or c["id"] >= 1306
}
suspicious_assignments = [
    product_row(p) for p in scope
    if (p.get("categ_id") and p["categ_id"][0] in suspicious_ids)
    or suspicious_ids.intersection(p.get("x_website_category_ids") or [])
]

category_usage = []
for c in categories:
    internal_count = usage_internal[c["id"]]
    website_count = usage_website[c["id"]]
    if internal_count or website_count:
        category_usage.append({
            "id": c["id"],
            "path": c.get("complete_name") or c["name"],
            "internal_products": internal_count,
            "website_products": website_count,
        })

report = {
    "counts": {
        "categories": len(categories),
        "all_templates": len(products),
        "active_sale_products": len(scope),
        "published_active_sale_products": len(published),
        "missing_custom_website_category": len(missing),
        "multiple_custom_website_categories": len(multi),
        "custom_category_does_not_include_internal": len(mismatch),
        "duplicate_active_product_name_groups": len(duplicate_products),
        "placeholder_named_products": len(placeholder_products),
        "duplicate_normalized_category_paths": len(duplicate_paths),
    },
    "root_categories": root_categories,
    "suspicious_assignments": suspicious_assignments,
    "duplicate_active_products": duplicate_products,
    "bird_categories": [
        {"id": c["id"], "path": c.get("complete_name") or c["name"]}
        for c in categories if 1102 <= c["id"] < 1116
    ],
}
print(json.dumps(report, indent=2))
