import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

# Test search_read with cashier user (uid=11)
# First let's authenticate as salesmasaki
uid_masaki = common.authenticate(db, 'salesmasaki@stephanspetstore.co.tz', 'Sales@3202', {})
if not uid_masaki:
    # Try with Sales Team Masaki password or find it
    print("Could not auth with Sales@3202")
else:
    print(f"Auth as salesmasaki: uid {uid_masaki}")
