import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

domain = [
    ('date_order', '>=', '2026-10-12 00:00:00'),
    ('date_order', '<=', '2026-10-17 23:59:59'),
    ('state', 'in', ['paid', 'invoiced', 'done']),
]

orders = models.execute_kw(db, uid, password, 'pos.order', 'search_read', [domain], {
    'fields': ['id', 'name', 'amount_total', 'date_order', 'config_id']
})

print(f"Total matching orders: {len(orders)}")
print(f"Total amount: {sum(o['amount_total'] for o in orders):,.2f}")
by_shop = {}
for o in orders:
    by_shop.setdefault(o['config_id'][1], []).append(o['amount_total'])

for shop, amts in by_shop.items():
    print(f"  {shop}: {len(amts)} orders -> {sum(amts):,.2f}")
