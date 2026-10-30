import xmlrpc.client

# Odoo connection details
url = "https://erp.stephanspetstore.co.tz"
db = "Stephans"
username = "info@stephanspetstore.co.tz"
password = "Stephan@3202"

print("[1/2] Connecting to Odoo...")
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

if not uid:
    print("[X] Authentication failed")
    exit(1)

print(f"[OK] Connected as user ID: {uid}")
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("\n[2/2] Searching for field 'Default language'...")
# Search ir.model.fields
fields = models.execute_kw(db, uid, password,
    'ir.model.fields', 'search_read',
    [[['field_description', 'ilike', 'Default language']]],
    {'fields': ['name', 'model', 'field_description']}
)

print(f"Found {len(fields)} matching fields:")
for f in fields:
    print(f"- Model: {f['model']} | Field: {f['name']} | Label: {f['field_description']}")

print("\nSearching for field 'Languages'...")
fields = models.execute_kw(db, uid, password,
    'ir.model.fields', 'search_read',
    [[['field_description', '=ilike', 'Languages']]], # Exact match for "Languages"
    {'fields': ['name', 'model', 'field_description']}
)

for f in fields:
    print(f"- Model: {f['model']} | Field: {f['name']} | Label: {f['field_description']}")
