import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

w42_orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [
    [('date_order', '>=', '2026-10-11 00:00:00'), ('date_order', '<', '2026-10-18 00:00:00')]
], {
    'fields': ['id', 'name', 'amount_total', 'date_order', 'create_date'],
    'order': 'date_order asc'
})

by_create_day = {}
for o in w42_orders:
    day = o['create_date'][:10]
    by_create_day.setdefault(day, []).append(o)

for day, d_orders in sorted(by_create_day.items()):
    print(f"Create Date: {day} | Count: {len(d_orders)} | Total: {sum(x['amount_total'] for x in d_orders):,.2f}")

