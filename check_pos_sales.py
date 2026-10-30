import xmlrpc.client
from datetime import datetime

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print(f"Authenticated as uid: {uid}")

# 1. Search for recent POS sessions
sessions = models.execute_kw(db, uid, password, 'pos.session', 'search_read', [
    [('start_at', '>=', '2026-10-10 00:00:00')]
], {
    'fields': ['id', 'name', 'state', 'start_at', 'stop_at', 'user_id', 'config_id', 'total_payments_amount', 'order_count'],
    'order': 'id desc'
})

print("=== RECENT POS SESSIONS ===")
for s in sessions:
    print(s)

# 2. Search for orders around 5,651,000 or total around that
# Or check orders created recently or last week
orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('date_order', '>=', '2026-10-10 00:00:00')]
], {
    'fields': ['id', 'name', 'pos_reference', 'state', 'session_id', 'amount_total', 'date_order', 'user_id'],
    'order': 'id desc',
    'limit': 50
})

print(f"\n=== RECENT POS ORDERS (Found {len(orders)}) ===")
total_recent = sum(o['amount_total'] for o in orders)
print(f"Total amount of recent orders: {total_recent}")
for o in orders[:15]:
    print(o)

# 3. Search specifically for any order or session matching 5651000 or active=False
orders_by_amt = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('amount_total', '>=', 5000000), ('amount_total', '<=', 6000000)]
], {
    'fields': ['id', 'name', 'amount_total', 'date_order', 'state', 'session_id']
})
print("\n=== ORDERS WITH AMOUNT ~ 5.65M ===")
print(orders_by_amt)

# Check active=False orders
archived_orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('active', '=', False)]
], {
    'fields': ['id', 'name', 'amount_total', 'date_order', 'state'],
    'limit': 20
}) if 'active' in models.execute_kw(db, uid, password, 'pos.order', 'fields_get', [], {'attributes': ['type']}) else "No active field on pos.order"

print("\n=== ARCHIVED ORDERS ===")
print(archived_orders)
