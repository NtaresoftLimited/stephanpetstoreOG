import xmlrpc.client
import ssl

# Ignore SSL certificate verification
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

url = "https://erp.stephanspetstore.co.tz"
db = "Stephans"
username = "info@stephanspetstore.co.tz"
password = "Stephan@3202"

common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', context=ctx)
uid = common.authenticate(db, username, password, {})

models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', context=ctx)

# Get the view
res = models.execute_kw(db, uid, password, 'ir.ui.view', 'search_read', [[['key', '=', 'grooming.grooming_appointment_view_form']]], {'fields': ['arch'], 'limit': 1})

if not res:
    # Try searching by name if key not found (sometimes key is not set for custom modules the same way)
    # Actually for XML data, 'key' field holds the xml_id if loaded? No, 'key' is usually for inherited views.
    # The XML ID is stored in ir.model.data.
    
    # Let's search by name
    res = models.execute_kw(db, uid, password, 'ir.ui.view', 'search_read', [[['name', '=', 'grooming.appointment.form']]], {'fields': ['arch'], 'limit': 1})

if res:
    print(res[0]['arch'])
else:
    print("View not found")
