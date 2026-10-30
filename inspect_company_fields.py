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

print("\n[2/2] Inspecting res.company fields...")
fields = models.execute_kw(db, uid, password,
    'res.company', 'fields_get',
    [],
    {'attributes': ['string', 'help', 'type']}
)

# Search for lang fields
print("\nLanguage fields in res.company:")
for field, data in fields.items():
    if 'lang' in field or 'code' in field:
         print(f"- {field}: {data['string']} ({data['type']})")

