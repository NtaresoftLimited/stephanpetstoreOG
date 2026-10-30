import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Fetch the last 15 orders in session 603
orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('session_id', '=', 603)]
], {
    'fields': ['id', 'name', 'pos_reference', 'amount_total', 'date_order', 'create_date', 'user_id'],
    'order': 'id desc',
    'limit': 15
})

print("Last 15 orders in session 603:")
for o in orders:
    print(o)
