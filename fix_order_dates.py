import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# List of orders to fix date_order to match create_date
order_ids = [3442, 3444, 3445, 3446, 3447, 3448, 3449, 3450, 3451, 3452, 3453, 3454, 3455, 3456, 3457]

orders = models.execute_kw(db, uid, password, 'pos.order', 'read', [order_ids], {'fields': ['id', 'name', 'create_date', 'date_order']})

print("Before fix:")
for o in orders:
    print(f"ID {o['id']}: {o['name']} | create_date: {o['create_date']} | date_order: {o['date_order']}")

# Update date_order = create_date for each
for o in orders:
    models.execute_kw(db, uid, password, 'pos.order', 'write', [[o['id']], {'date_order': o['create_date']}])

print("\nSuccessfully updated date_order to match create_date!")

# Verify after fix
orders_after = models.execute_kw(db, uid, password, 'pos.order', 'read', [order_ids], {'fields': ['id', 'name', 'create_date', 'date_order']})
print("\nAfter fix:")
for o in orders_after:
    print(f"ID {o['id']}: {o['name']} | create_date: {o['create_date']} | date_order: {o['date_order']}")
