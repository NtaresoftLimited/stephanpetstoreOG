import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Check today's orders
today_orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('id', 'in', [3455, 3456, 3457])]
], {
    'fields': ['id', 'name', 'session_id', 'amount_total', 'payment_ids']
})
print("Today's orders:", today_orders)

for o in today_orders:
    payments = models.execute_kw(db, uid, password, 'pos.payment', 'read', [o['payment_ids']], {
        'fields': ['id', 'session_id', 'amount', 'payment_method_id']
    })
    print(f"Payments for order {o['id']}:", payments)
