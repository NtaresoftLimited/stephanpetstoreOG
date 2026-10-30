import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Read rules 764 and 926
rules = models.execute_kw(db, uid, password, 'ir.rule', 'read', [[764, 926]], {'fields': ['id', 'name', 'domain_force', 'groups', 'active']})
print("Rule details:", rules)
