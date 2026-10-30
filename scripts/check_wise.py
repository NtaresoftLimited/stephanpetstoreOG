import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

res = models.execute_kw(db, uid, password, 'ir.module.module', 'search_read', [[('name', '=', 'wise_pos_stock')]], {'fields': ['name', 'state', 'latest_version']})
print("wise_pos_stock status:", res)
