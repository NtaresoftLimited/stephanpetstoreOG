import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Verify configs
configs = models.execute_kw(db, uid, password, 'pos.config', 'search_read', [
    [('id', 'in', [5, 7])]
], {'fields': ['id', 'name', 'warehouse_id', 'picking_type_id']})

print("=== VERIFIED POS CONFIGS ===")
for c in configs:
    print(c)
