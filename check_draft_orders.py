import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Read session 603 details
session_fields = ['id', 'name', 'state', 'rescue', 'order_ids', 'order_count', 'total_payments_amount']
s603 = models.execute_kw(db, uid, password, 'pos.session', 'read', [[603]], {'fields': session_fields})[0]
print("Session 603 state:", s603['state'])

# Check if there are any draft/unpaid orders in session 603
draft_orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('session_id', '=', 603), ('state', 'not in', ['paid', 'invoiced', 'done'])]
], {'fields': ['id', 'name', 'state', 'amount_total']})
print("Draft / unpaid orders in session 603:", draft_orders)

# Also check session 602
draft_orders_602 = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('session_id', '=', 602), ('state', 'not in', ['paid', 'invoiced', 'done'])]
], {'fields': ['id', 'name', 'state', 'amount_total']})
print("Draft / unpaid orders in session 602:", draft_orders_602)

# Check all draft pos.order across the entire database
all_draft_orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('state', 'in', ['draft'])]
], {'fields': ['id', 'name', 'session_id', 'state', 'amount_total', 'create_date']})
print("\nAll draft POS orders across DB:", all_draft_orders)

