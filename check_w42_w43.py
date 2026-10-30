import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Orders in W42: date_order >= 2026-10-11 00:00:00 and date_order < 2026-10-18 00:00:00
w42_orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('date_order', '>=', '2026-10-11 00:00:00'), ('date_order', '<', '2026-10-18 00:00:00')]
], {
    'fields': ['id', 'name', 'amount_total', 'date_order', 'create_date', 'session_id', 'config_id'],
    'order': 'date_order asc'
})

print(f"W42 orders count: {len(w42_orders)}, sum: {sum(o['amount_total'] for o in w42_orders):,.2f}")

# Orders in W43: date_order >= 2026-10-18 00:00:00
w43_orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('date_order', '>=', '2026-10-18 00:00:00')]
], {
    'fields': ['id', 'name', 'amount_total', 'date_order', 'create_date', 'session_id', 'config_id'],
    'order': 'date_order asc'
})

print(f"W43 orders count: {len(w43_orders)}, sum: {sum(o['amount_total'] for o in w43_orders):,.2f}")
print("\nW43 orders detail:")
for o in w43_orders:
    print(f"ID: {o['id']} | {o['name']} | Total: {o['amount_total']:10,.2f} | date_order: {o['date_order']} | create_date: {o['create_date']}")

