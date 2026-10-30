import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# 1. Check groups for cashiers / sales team users
users = models.execute_kw(db, uid, password, 'res.users', 'search_read', [
    [('login', 'in', ['sales_masaki', 'sales_mikocheni', 'Sales Team Masaki', 'Sales Team Mikocheni'])]
], {'fields': ['id', 'name', 'login', 'groups_id']})
if not users:
    users = models.execute_kw(db, uid, password, 'res.users', 'search_read', [
        [('name', 'ilike', 'Sales Team')]
    ], {'fields': ['id', 'name', 'login', 'groups_id']})

print("Cashier Users:", users)

# 2. Check record rules on pos.order
rules = models.execute_kw(db, uid, password, 'ir.rule', 'search_read', [
    [('model_id.model', '=', 'pos.order')]
], {'fields': ['id', 'name', 'domain_force', 'groups', 'active']})
print("\nRecord rules on pos.order:")
for r in rules:
    print(r)

# 3. Check simplify_access_management or any custom domain rules
sam = models.execute_kw(db, uid, password, 'ir.model', 'search_read', [
    [('model', 'ilike', 'simplify_access')]
], {'fields': ['model', 'name']})
print("\nSimplify access models:", sam)
