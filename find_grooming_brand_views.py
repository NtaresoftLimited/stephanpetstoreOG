import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

v = models.execute_kw(db, uid, password, 'ir.ui.view', 'read', [[12454]], {'fields': ['id', 'name', 'inherit_children_ids']})
print("View 12454:", v)

# Also search for any view containing brand_id and grooming.service
views = models.execute_kw(db, uid, password, 'ir.ui.view', 'search_read', [
    [('model', '=', 'grooming.service'), ('arch_db', 'ilike', 'brand_id')]
], {'fields': ['id', 'name', 'arch_db']})
print("All grooming.service views with brand_id:", views)
