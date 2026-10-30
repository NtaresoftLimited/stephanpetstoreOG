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

print("\n[2/2] Fetching view for pos.config...")
# Find the form view for pos.config
view_id = models.execute_kw(db, uid, password,
    'ir.ui.view', 'search',
    [[['model', '=', 'pos.config'], ['type', '=', 'form']]]
)

if not view_id:
    print("[X] No form view found for pos.config")
    exit(1)
    
# Get the view architecture (XML)
views = models.execute_kw(db, uid, password,
    'ir.ui.view', 'read',
    [view_id],
    {'fields': ['arch']}
)

for view in views:
    print(f"\n--- View XML ---")
    print(view['arch'])

# Save to file
with open('pos_config_view.xml', 'w', encoding='utf-8') as f:
    for view in views:
        f.write(view['arch'])
        
print("\nSaved view to pos_config_view.xml")
