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

print("\n[2/2] Inspecting pos.config fields...")
# Get all fields for pos.config
fields = models.execute_kw(db, uid, password,
    'pos.config', 'fields_get',
    [],
    {'attributes': ['string', 'help', 'type']}
)

# Filter for language related fields
lang_fields = {k: v for k, v in fields.items() if 'lang' in k}

print("\nFound language-related fields:")
for field, data in lang_fields.items():
    print(f"- {field}: {data['string']} ({data['type']})")
    
# Also check if there are other relevant fields
print("\nChecking for 'localization' fields:")
loc_fields = {k: v for k, v in fields.items() if 'loc' in k}
for field, data in loc_fields.items():
    print(f"- {field}: {data['string']} ({data['type']})")

