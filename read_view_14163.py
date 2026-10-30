import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

v = models.execute_kw(db, uid, password, 'ir.ui.view', 'read', [[14163]], {'fields': ['id', 'name', 'arch_db', 'inherit_id', 'active']})
print("View 14163:", v)
