import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

v = models.execute_kw(db, uid, password, 'ir.ui.view', 'search_read', [
    [('model', '=', 'pos.order'), ('type', '=', 'search')]
], {'fields': ['id', 'name', 'arch_db']})

print("POS Order Search Views:")
for x in v:
    print(f"\n--- ID {x['id']}: {x['name']} ---")
    print(x['arch_db'])
