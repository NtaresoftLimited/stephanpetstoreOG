import xmlrpc.client
import json

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

print("\n[2/2] Getting all fields...")
fields = models.execute_kw(db, uid, password,
    'pos.config', 'fields_get',
    [],
    {'attributes': ['string', 'help', 'type']}
)

# Sort by name
sorted_fields = dict(sorted(fields.items()))

# Write to file
with open('pos_config_fields.txt', 'w', encoding='utf-8') as f:
    for field, data in sorted_fields.items():
        f.write(f"{field}: {data['string']} ({data['type']})\n")

print("Saved to pos_config_fields.txt")
