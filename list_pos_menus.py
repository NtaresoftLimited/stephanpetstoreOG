import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Find all menus under point_of_sale
pos_root = models.execute_kw(db, uid, password, 'ir.ui.menu', 'search_read', [
    [('name', 'ilike', 'Point of Sale')]
], {'fields': ['id', 'name', 'parent_id', 'action']})

print("POS Root menus:", pos_root)

all_pos_menus = models.execute_kw(db, uid, password, 'ir.ui.menu', 'search_read', [
    [('parent_id', 'child_of', [m['id'] for m in pos_root])]
], {'fields': ['id', 'name', 'parent_id', 'action', 'active'], 'order': 'parent_id asc, sequence asc'})

print("\nAll POS Submenus:")
for m in all_pos_menus:
    print(f"ID {m['id']}: {m['name']} (Active: {m['active']}) -> Action: {m['action']}")
