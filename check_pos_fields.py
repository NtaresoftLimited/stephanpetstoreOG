import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

field_info = models.execute_kw(db, uid, password, 'pos.config', 'fields_get', [['warehouse_id', 'picking_type_id']], {'attributes': ['type', 'related', 'readonly', 'store']})
print("Field info on pos.config:", field_info)

# Let's inspect pos.config 7
pos7 = models.execute_kw(db, uid, password, 'pos.config', 'read', [[7]], {'fields': ['id', 'name', 'warehouse_id', 'picking_type_id']})[0]
print("POS 7:", pos7)

# Let's inspect picking type 36
pt36 = models.execute_kw(db, uid, password, 'stock.picking.type', 'read', [[36]], {'fields': ['id', 'name', 'warehouse_id']})[0]
print("Picking type 36:", pt36)
