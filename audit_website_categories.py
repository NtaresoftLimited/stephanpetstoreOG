import json
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


template_fields = call(
    "product.template",
    "fields_get",
    [],
    {"attributes": ["string", "type", "relation", "store"]},
)
interesting = {
    name: spec
    for name, spec in template_fields.items()
    if any(token in name.lower() for token in ("categ", "website", "publish"))
}
print("PRODUCT TEMPLATE CATEGORY/WEBSITE FIELDS")
print(json.dumps(interesting, indent=2, sort_keys=True))

for model in ("product.public.category", "product.category"):
    fields = call(model, "fields_get", [], {"attributes": ["string", "type", "relation", "store"]})
    wanted = {
        name: fields[name]
        for name in fields
        if name in {"name", "display_name", "complete_name", "parent_id", "child_id", "website_id", "is_published", "active"}
    }
    count = call(model, "search_count", [[]])
    print(f"\n{model}: {count} records")
    print(json.dumps(wanted, indent=2, sort_keys=True))

field_names = ["name", "active", "sale_ok", "categ_id"]
for optional in ("default_code", "public_categ_ids", "website_id", "is_published", "website_published"):
    if optional in template_fields:
        field_names.append(optional)

products = call(
    "product.template",
    "search_read",
    [[]],
    {"fields": field_names, "order": "id", "context": {"active_test": False}},
)
print(f"\nPRODUCT TEMPLATES: {len(products)}")

for field_name in ("public_categ_ids", "categ_id"):
    if field_name not in template_fields:
        continue
    missing = [p for p in products if not p.get(field_name)]
    print(f"Missing {field_name}: {len(missing)}")
    print(json.dumps([{"id": p["id"], "name": p["name"], "active": p["active"]} for p in missing[:100]], indent=2))

if "public_categ_ids" in template_fields:
    relation = template_fields["public_categ_ids"].get("relation")
    all_ids = sorted({cat_id for p in products for cat_id in (p.get("public_categ_ids") or [])})
    categories = call(relation, "read", [all_ids], {"fields": ["name", "display_name", "parent_id"]}) if all_ids else []
    print(f"Assigned {relation} records: {len(categories)}")
    print(json.dumps(categories, indent=2))

category_fields = call("product.category", "fields_get", [], {"attributes": ["string", "type", "relation", "store"]})
cat_read_fields = [name for name in ("name", "display_name", "complete_name", "parent_id", "active", "website_id", "is_published") if name in category_fields]
categories = call(
    "product.category",
    "search_read",
    [[]],
    {"fields": cat_read_fields, "order": "id", "context": {"active_test": False}},
)
print(f"\nALL PRODUCT CATEGORIES: {len(categories)}")
print(json.dumps(categories, indent=2))
