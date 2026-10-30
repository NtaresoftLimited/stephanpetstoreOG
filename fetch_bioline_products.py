#!/usr/bin/env python3
"""Fetch Bioline products from Odoo using correct brand_id field."""
import xmlrpc.client, json, sys
sys.stdout.reconfigure(encoding="utf-8")

ODOO_URL  = "https://erp.stephanspetstore.co.tz"
ODOO_DB   = "Stephans"
ODOO_USER = "info@stephanspetstore.co.tz"
ODOO_PASS = "Stephan@3202"

common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

products = models.execute_kw(ODOO_DB, uid, ODOO_PASS,
    "product.template", "search_read",
    [[["brand_id", "=", 2], ["active", "=", True]]],
    {"fields": ["id", "name", "list_price", "default_code", "qty_available"], "limit": 200}
)
print(f"Bioline products: {len(products)}")
for p in products[:15]:
    print(f"  {p['default_code'] or '---':12s} | {p['name'][:45]:45s} | {p['list_price']:>10,.0f}")
if len(products) > 15:
    print(f"  ... +{len(products)-15} more")

with open("bioline_products.json", "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=2)
print(f"\nSaved {len(products)} products to bioline_products.json")
