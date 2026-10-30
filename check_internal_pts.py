import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

pts = models.execute_kw(db, uid, password, 'stock.picking.type', 'search_read', [
    [('code', '=', 'internal')]
], {
    'fields': ['id', 'name', 'warehouse_id', 'default_location_src_id', 'default_location_dest_id']
})

print("Internal Picking Types:")
for pt in pts:
    print(pt)
