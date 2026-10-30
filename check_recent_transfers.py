import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Check recent stock requests
requests = models.execute_kw(db, uid, password, 'grooming.stock.request', 'search_read', [[]], {
    'fields': ['id', 'name', 'source_warehouse_id', 'destination_warehouse_id', 'create_uid', 'create_date', 'state'],
    'order': 'id desc',
    'limit': 10
})
print("=== RECENT REPLENISHMENT REQUESTS (grooming.stock.request) ===")
for r in requests:
    print(r)

# Check recent internal transfers (stock.picking)
pickings = models.execute_kw(db, uid, password, 'stock.picking', 'search_read', [
    [('picking_type_code', '=', 'internal')]
], {
    'fields': ['id', 'name', 'location_id', 'location_dest_id', 'custom_source_warehouse_id', 'custom_destination_warehouse_id', 'create_uid', 'create_date', 'state'],
    'order': 'id desc',
    'limit': 10
})
print("\n=== RECENT INTERNAL TRANSFERS (stock.picking) ===")
for p in pickings:
    print(p)

