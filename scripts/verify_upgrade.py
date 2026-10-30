import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print(f"Authenticated as Admin (uid {uid})")

# Find module IDs
module_ids = models.execute_kw(db, uid, password, 'ir.module.module', 'search', [[('name', 'in', ['grooming', 'custom_pos_reports'])]])
print(f"Found module IDs: {module_ids}")

# Upgrade modules
print("Triggering immediate upgrade via XML-RPC...")
res = models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_upgrade', [module_ids])
print("Upgrade completed successfully!")

# Now check ir.rule 926
rule = models.execute_kw(db, uid, password, 'ir.rule', 'read', [[926]], {'fields': ['name', 'domain_force', 'active']})
print("Rule 926:", rule)

# Now check cashier view of pos.order
# Authenticate as salesmasaki
uid_cashier = common.authenticate(db, 'salesmasaki@stephanspetstore.co.tz', 'Sales@3202', {})
if not uid_cashier:
    print("Finding cashier user...")
    users = models.execute_kw(db, uid, password, 'res.users', 'search_read', [[('login', 'like', 'masaki')]], {'fields': ['id', 'name', 'login']})
    print("Users found:", users)
else:
    print(f"Authenticated as cashier (uid {uid_cashier})")
    # Search orders from last week
    orders = models.execute_kw(db, uid_cashier, 'Sales@3202', 'pos.order', 'search_read', [
        [('date_order', '>=', '2026-10-12 00:00:00'), ('date_order', '<=', '2026-10-18 23:59:59')]
    ], {'fields': ['name', 'date_order', 'amount_total', 'state']})
    print(f"Cashier can see {len(orders)} orders from last week!")
    total = sum(o['amount_total'] for o in orders)
    print(f"Total sales visible to cashier from last week: {total:,.2f} TZS")
