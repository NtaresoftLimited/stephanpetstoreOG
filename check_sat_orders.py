import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('id', 'in', list(range(3442, 3458)))]
], {
    'fields': ['id', 'name', 'amount_total', 'create_date', 'date_order']
})

for o in orders:
    print(f"ID: {o['id']} | {o['name']} | Total: {o['amount_total']} | create_date: {o['create_date']} | date_order: {o['date_order']}")
