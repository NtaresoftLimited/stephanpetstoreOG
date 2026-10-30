import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Read current pos.config for Mikocheni
cfg7 = models.execute_kw(db, uid, password, 'pos.config', 'read', [[7]], {'fields': ['id', 'name', 'warehouse_id', 'picking_type_id']})[0]
print("Before update:", cfg7)

# Update pos.config 7 warehouse_id to 3 (Mikocheni)
models.execute_kw(db, uid, password, 'pos.config', 'write', [[7], {'warehouse_id': 3}])
print("Updated pos.config 7 warehouse_id to 3!")

cfg7_after = models.execute_kw(db, uid, password, 'pos.config', 'read', [[7]], {'fields': ['id', 'name', 'warehouse_id', 'picking_type_id']})[0]
print("After update:", cfg7_after)
