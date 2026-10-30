import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

session = models.execute_kw(db, uid, password, 'pos.session', 'read', [[603]], {
    'fields': ['id', 'name', 'state', 'start_at', 'stop_at', 'order_count', 'total_payments_amount']
})[0]

print("Session 603:", session)
