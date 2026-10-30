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


def call(method, args=None, kwargs=None):
    return models.execute_kw(DB, uid, PASSWORD, "product.template", method, args or [], kwargs or {})


products = call(
    "search_read",
    [[("active", "=", True), ("sale_ok", "=", True)]],
    {"fields": ["name", "categ_id", "x_website_category_ids"], "order": "id"},
)
updates = [p for p in products if p["x_website_category_ids"] != [p["categ_id"][0]]]
print(json.dumps({"active_sale_products": len(products), "updates": len(updates)}, indent=2))

for product in updates:
    call("write", [[product["id"]], {"x_website_category_ids": [(6, 0, [product["categ_id"][0]])]}])

verified = call(
    "search_read",
    [[("active", "=", True), ("sale_ok", "=", True)]],
    {"fields": ["categ_id", "x_website_category_ids"]},
)
result = {
    "verified": len(verified),
    "missing": sum(not p["x_website_category_ids"] for p in verified),
    "multiple": sum(len(p["x_website_category_ids"]) > 1 for p in verified),
    "mismatch": sum(p["x_website_category_ids"] != [p["categ_id"][0]] for p in verified),
}
print(json.dumps(result, indent=2))
