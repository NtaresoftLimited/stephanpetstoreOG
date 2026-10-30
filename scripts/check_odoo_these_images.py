import xmlrpc.client

url = 'https://erp.stephanspetstore.co.tz'
db = 'Stephans'
username = 'info@stephanspetstore.co.tz'
password = 'Stephan@3202'

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

res = models.execute_kw(db, uid, password, 'product.template', 'read', [[1106, 2716, 2719]], {'fields': ['id', 'name', 'image_1920']})
for r in res:
    img = r.get('image_1920')
    print(f"ID {r['id']} ({r['name']}): has_image={bool(img)}, length={len(img) if img else 0}")
