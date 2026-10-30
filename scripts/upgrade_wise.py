import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print("Upgrading wise_pos_stock...")
try:
    models.execute_kw(db, uid, password, 'ir.module.module', 'button_immediate_upgrade', [[1250]])
    print("wise_pos_stock upgraded successfully!")
except Exception as e:
    print("Upgrade error:", e)
