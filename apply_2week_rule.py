import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Use time module which is supported in safe_eval
# 14 days = 14 * 86400 = 1209600 seconds
domain_2_weeks = "[('date_order', '>=', time.strftime('%Y-%m-%d 00:00:00', time.localtime(time.time() - 14 * 86400)))]"

# Update rule 926
models.execute_kw(db, uid, password, 'ir.rule', 'write', [[926], {
    'name': 'POS Order: Last 2 Weeks for POS Users',
    'domain_force': domain_2_weeks,
    'active': True
}])
print("Updated rule 926 to 2 weeks domain successfully!")

# Delete rule 764 if exists
rules_764 = models.execute_kw(db, uid, password, 'ir.rule', 'search_read', [
    [('id', '=', 764)]
], {'fields': ['id', 'name']})

if rules_764:
    models.execute_kw(db, uid, password, 'ir.rule', 'unlink', [[764]])
    print("Deleted duplicate rule 764!")

# Verify active rules
active_rules = models.execute_kw(db, uid, password, 'ir.rule', 'search_read', [
    [('model_id.model', '=', 'pos.order'), ('active', '=', True)]
], {'fields': ['id', 'name', 'domain_force', 'groups']})
print("\nActive POS Order Rules now:")
for r in active_rules:
    print(r)
