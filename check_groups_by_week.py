import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Read group by date_order:week
groups = models.execute_kw(db, uid, password, 'pos.order', 'read_group', [
    [],
    ['amount_total'],
    ['date_order:week']
], {
    'orderby': 'date_order:week desc',
    'limit': 10
})

print("Groups by week:")
for g in groups:
    print(g)
