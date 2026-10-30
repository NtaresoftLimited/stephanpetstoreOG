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

print("\n[2/2] Inspecting pos.session fields...")
fields = models.execute_kw(db, uid, password,
    'pos.session', 'fields_get',
    [],
    {'attributes': ['string', 'type']}
)

# Search for balance or cash related fields
print("\nPossible balance/cash fields:")
for field, data in fields.items():
    if 'balance' in field or 'cash' in field:
         print(f"- {field}: {data['string']} ({data['type']})")

