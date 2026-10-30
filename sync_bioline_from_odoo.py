#!/usr/bin/env python3
"""
Sync Bioline brand logo + products from Odoo to Sanity.
- Uploads Bioline logo to Sanity and sets it on the brand document
- Outputs product list to bioline_products.json for review
"""
import xmlrpc.client, base64, json, sys
sys.stdout.reconfigure(encoding="utf-8")

ODOO_URL = "https://erp.stephanspetstore.co.tz"
ODOO_DB  = "Stephans"
ODOO_USER = "info@stephanspetstore.co.tz"
ODOO_PASS = "Stephan@3202"

SANITY_PROJECT = "ubqcgegx"
SANITY_DATASET = "production"
SANITY_TOKEN   = "skRVcjqvX5f0XYnDxDLTriPEKGptCwVM7rhH59su5uIZ9XM8XJmbyPBbAvV6fUT4vEq9OoSjMpZBR9QKXEdGy1fgQTd09YnylrDJaa992PpojpHHxT0umVx68OiCAHfgfhoogExv6buhwB497xFAHgfc2M40Mrt3GeFfTQ3njuyHVEdS6FtN"

# ── Odoo connect ────────────────────────────────────────────────────────────
common = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/common")
uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASS, {})
models = xmlrpc.client.ServerProxy(f"{ODOO_URL}/xmlrpc/2/object")

# ── Fetch Bioline brand ─────────────────────────────────────────────────────
brands = models.execute_kw(ODOO_DB, uid, ODOO_PASS,
    "product.brand", "search_read",
    [[["name", "ilike", "Bioline"]]],
    {"fields": ["id", "name", "logo"], "limit": 1}
)
if not brands:
    print("Bioline brand not found in Odoo!"); sys.exit(1)

brand = brands[0]
print(f"Found brand: {brand['name']} (ID={brand['id']})")
has_logo = bool(brand.get("logo"))
print(f"Has logo: {has_logo}")

# ── Upload logo to Sanity ───────────────────────────────────────────────────
if has_logo:
    import urllib.request, urllib.error
    logo_bytes = base64.b64decode(brand["logo"])
    
    upload_url = f"https://api.sanity.io/v2021-03-25/assets/images/{SANITY_PROJECT}/{SANITY_DATASET}?filename=bioline-logo.png"
    req = urllib.request.Request(
        upload_url,
        data=logo_bytes,
        headers={
            "Authorization": f"Bearer {SANITY_TOKEN}",
            "Content-Type": "image/png",
        },
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            asset_id = result["document"]["_id"]
            print(f"Logo uploaded to Sanity: {asset_id}")
    except urllib.error.HTTPError as e:
        print(f"Upload error: {e.code} {e.read()}")
        sys.exit(1)

    # Update Sanity brand document with logo
    sanity_query_url = f"https://ubqcgegx.api.sanity.io/v2021-03-25/data/query/{SANITY_DATASET}?query=*[_type==\"brand\"&&name==\"Bioline\"][0]{{_id}}"
    req2 = urllib.request.Request(sanity_query_url, headers={"Authorization": f"Bearer {SANITY_TOKEN}"})
    with urllib.request.urlopen(req2) as r:
        q = json.loads(r.read())
    
    brand_doc_id = q.get("result", {}).get("_id") if q.get("result") else None
    if not brand_doc_id:
        print("Bioline brand not found in Sanity - cannot update logo"); 
    else:
        print(f"Sanity brand doc: {brand_doc_id}")
        mutations = json.dumps({"mutations": [{"patch": {
            "id": brand_doc_id,
            "set": {"logo": {"_type": "image", "asset": {"_type": "reference", "_ref": asset_id}}}
        }}]}).encode()
        req3 = urllib.request.Request(
            f"https://ubqcgegx.api.sanity.io/v2021-03-25/data/mutate/{SANITY_DATASET}",
            data=mutations,
            headers={"Authorization": f"Bearer {SANITY_TOKEN}", "Content-Type": "application/json"},
            method="POST"
        )
        with urllib.request.urlopen(req3) as r:
            res = json.loads(r.read())
            print("Logo set on Sanity brand:", res.get("results", [{}])[0].get("operation"))

# ── Fetch Bioline products from Odoo ───────────────────────────────────────
products = models.execute_kw(ODOO_DB, uid, ODOO_PASS,
    "product.template", "search_read",
    [[["product_brand_id", "=", brand["id"]], ["active", "=", True]]],
    {"fields": ["id", "name", "list_price", "default_code", "qty_available"], "limit": 200}
)
print(f"\nFound {len(products)} Bioline products in Odoo")
for p in products[:10]:
    print(f"  {p['default_code'] or '---'} | {p['name']} | TSh {p['list_price']:,.0f}")
if len(products) > 10:
    print(f"  ... and {len(products)-10} more")

# Save full list
with open("bioline_products.json", "w", encoding="utf-8") as f:
    json.dump(products, f, ensure_ascii=False, indent=2)
print("\nFull product list saved to bioline_products.json")
