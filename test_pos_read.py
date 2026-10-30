import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Read config 7 as POS does
configs = models.execute_kw(db, uid, password, 'pos.config', 'read', [[7]], {'fields': ['warehouse_id']})
print("Mikocheni POS config read result:", configs)
dest_id = configs[0]['warehouse_id'][0]
dest_name = configs[0]['warehouse_id'][1]
print(f"Destination Warehouse ID: {dest_id}, Name: {dest_name}")

# Read config 5 (Masaki)
configs_masaki = models.execute_kw(db, uid, password, 'pos.config', 'read', [[5]], {'fields': ['warehouse_id']})
print("Masaki POS config read result:", configs_masaki)
