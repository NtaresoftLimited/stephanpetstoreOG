import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Find grooming module
mods = models.execute_kw(db, uid, password, 'ir.module.module', 'search_read', [
    [('name', '=', 'grooming')]
], {'fields': ['id', 'name', 'state']})

print("Grooming module:", mods)
if mods:
    mod_id = mods[0]['id']
    models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_upgrade', [[mod_id]])
    print("Successfully upgraded grooming module via XML-RPC!")
