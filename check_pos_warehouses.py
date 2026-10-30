import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# 1. Check all warehouses
warehouses = models.execute_kw(db, uid, password, 'stock.warehouse', 'search_read', [[]], {
    'fields': ['id', 'name', 'code', 'lot_stock_id', 'view_location_id']
})
print("=== WAREHOUSES ===")
for wh in warehouses:
    print(wh)

# 2. Check pos.config for all POS
pos_configs = models.execute_kw(db, uid, password, 'pos.config', 'search_read', [[]], {
    'fields': ['id', 'name', 'warehouse_id', 'picking_type_id']
})
print("\n=== POS CONFIGS ===")
for pc in pos_configs:
    print(pc)

# 3. Check picking_type_id details
for pc in pos_configs:
    if pc['picking_type_id']:
        pt = models.execute_kw(db, uid, password, 'stock.picking.type', 'read', [[pc['picking_type_id'][0]]], {
            'fields': ['id', 'name', 'warehouse_id', 'default_location_src_id', 'default_location_dest_id']
        })[0]
        print(f"\nPicking Type for POS '{pc['name']}':", pt)

