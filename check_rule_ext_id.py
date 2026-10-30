import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

data = models.execute_kw(db, uid, password, 'ir.model.data', 'search_read', [
    [('model', '=', 'ir.rule'), ('res_id', 'in', [764, 926])]
], {'fields': ['id', 'module', 'name', 'res_id']})

print("External IDs:", data)
