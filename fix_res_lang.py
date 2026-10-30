import xmlrpc.client

# Odoo connection details
url = "https://erp.stephanspetstore.co.tz"
db = "Stephans"
username = "info@stephanspetstore.co.tz"
password = "Stephan@3202"

print("[1/3] Connecting to Odoo...")
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})

if not uid:
    print("[X] Authentication failed")
    exit(1)

print(f"[OK] Connected as user ID: {uid}")
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("\n[2/3] Checking Languages...")
# Search for all languages
langs = models.execute_kw(db, uid, password,
    'res.lang', 'search_read',
    [],
    {'fields': ['name', 'code', 'active']}
)

print(f"Found {len(langs)} languages:")
english_found = False
for lang in langs:
    status = "Active" if lang['active'] else "Inactive"
    print(f"- {lang['name']} ({lang['code']}): {status}")
    if lang['code'] == 'en_US':
        english_found = True
        if not lang['active']:
            print("  -> ACTIVATING English...")
            models.execute_kw(db, uid, password,
                'res.lang', 'write',
                [[lang['id']], {'active': True}]
            )
            print("  -> ACTIVATED.")

if not english_found:
    print("\n[X] English (en_US) not found! You need to install it.")
    # In some versions we can't install via RPC easily without loading a module
    
print("\n[3/3] Checking if 'pos_restaurant' or 'pos_iot' adds language fields...")
# Sometimes modules inject fields.
# We already checked pos.config fields and didn't see language.

