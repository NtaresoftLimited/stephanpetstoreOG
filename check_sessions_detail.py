import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Read latest sessions
sessions = models.execute_kw(db, uid, password, 'pos.session', 'search_read', [
    []
], {
    'fields': ['id', 'name', 'state', 'start_at', 'stop_at', 'user_id', 'config_id', 'total_payments_amount', 'order_count'],
    'order': 'id desc',
    'limit': 15
})

print("=== LATEST POS SESSIONS ===")
for s in sessions:
    print(s)

# Read orders in session 603, 602, etc.
for s in sessions[:5]:
    orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
        [('session_id', '=', s['id'])]
    ], {
        'fields': ['id', 'name', 'pos_reference', 'state', 'amount_total', 'date_order'],
        'order': 'date_order desc'
    })
    total = sum(o['amount_total'] for o in orders)
    print(f"\nSession {s['id']} ({s['name']}) - State: {s['state']} - Total Orders: {len(orders)} - Sum of amounts: {total:,.2f}")
    if orders:
        print(f"  First order: {orders[-1]['date_order']} ({orders[-1]['name']})")
        print(f"  Last order: {orders[0]['date_order']} ({orders[0]['name']})")

