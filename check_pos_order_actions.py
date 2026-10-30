import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Check action for Point of Sale -> Orders
actions = models.execute_kw(db, uid, password, 'ir.actions.act_window', 'search_read', [
    [('res_model', '=', 'pos.order')]
], {
    'fields': ['id', 'name', 'context', 'domain', 'search_view_id']
})

print("POS Order Actions:")
for a in actions:
    print(a)

# Also check search view
search_views = models.execute_kw(db, uid, password, 'ir.ui.view', 'search_read', [
    [('model', '=', 'pos.order'), ('type', '=', 'search')]
], {
    'fields': ['id', 'name', 'arch_db']
})

print("\nSearch Views for pos.order:")
for sv in search_views:
    print(sv['id'], sv['name'])
