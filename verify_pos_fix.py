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

print("\n[2/2] Attempting valid write to POS config...")
# Find POS config
pos_configs = models.execute_kw(db, uid, password,
    'pos.config', 'search_read',
    [[['name', '=', "Stephan's Pet Store"]]],
    {'fields': ['id', 'name']}
)

if not pos_configs:
    print("[X] POS config not found")
    exit(1)

pos_id = pos_configs[0]['id']
print(f"Testing write on POS ID: {pos_id}")

try:
    # Just write the name back to itself to trigger validation
    models.execute_kw(db, uid, password,
        'pos.config', 'write',
        [[pos_id], {'name': "Stephan's Pet Store"}]
    )
    print("\n[OK] Write successful! logic validation passed.")
    print("The error should be gone now.")
except Exception as e:
    print(f"\n[X] Write failed: {e}")
