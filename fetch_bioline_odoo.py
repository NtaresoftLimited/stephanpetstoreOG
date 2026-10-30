#!/usr/bin/env python3
"""
Step 1: Fetch Bioline logo from Odoo and products list.
        Saves logo as bioline_logo.png and products as bioline_products.json
"""
import xmlrpc.client, base64, json, sys
sys.stdout.reconfigure(encoding="utf-8")

ODOO_URL  = "https://erp.stephanspetstore.co.tz"
ODOO_DB   = "Stephans"
ODOO_USER = "info@stephanspetstore.co.tz"
ODOO_PASS = "Stephan@3202"

common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

# Fetch Bioline brand with logo
brands = models.execute_kw(ODOO_DB, uid, ODOO_PASS,
    "product.brand", "search_read",
    [[["name", "ilike", "Bioline"]]],
    {"fields": ["id", "name", "logo"], "limit": 1}
)
brand = brands[0]
print(f"Brand: {brand['name']} (Odoo ID={brand['id']})")

# Save logo
if brand.get("logo"):
    logo_bytes = base64.b64decode(brand["logo"])
    with open("bioline_logo.png", "wb") as f:
        f.write(logo_bytes)
    print(f"Logo saved: bioline_logo.png ({len(logo_bytes):,} bytes)")
else:
    print("No logo found in Odoo.")

# Fetch all products
products = models.execute_kw(ODOO_DB, uid, ODOO_PASS,
    "product.template", "search_read",
    [[["product_brand_id", "=", brand["id"]], ["active", "=", True]]],
    {"fields": ["id", "name", "list_price", "default_code", "qty_available", "description_sale"], "limit": 200}
)
print(f"Products found: {len(products)}")
for p in products[:10]:
    print(f"  {p['default_code'] or '---':12s} | {p['name'][:45]:45s} | {p['list_price']:>10,.0f} TSh")
if len(products) > 10:
    print(f"  ... and {len(products)-10} more")

with open("bioline_products.json", "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=2)
print(f"\nSaved to bioline_products.json")
