import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Fetch the 55 orders from last week
orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('create_date', '>=', '2026-10-12 00:00:00'), ('create_date', '<=', '2026-10-18 23:59:59')]
], {
    'fields': ['id', 'name', 'amount_total', 'date_order', 'create_date', 'config_id'],
    'order': 'id asc'
})

print(f"Total: {len(orders)} orders, Total Amount: {sum(o['amount_total'] for o in orders):,.2f}")
print("\nOrders where date_order date differs from create_date date:")
diff_count = 0
for o in orders:
    c_date = o['create_date'][:10]
    d_date = o['date_order'][:10]
    if c_date != d_date:
        diff_count += 1
        print(f"ID {o['id']}: {o['name']} | Amount: {o['amount_total']} | create_date: {o['create_date']} | date_order: {o['date_order']}")

print(f"\nTotal with different date: {diff_count}")
