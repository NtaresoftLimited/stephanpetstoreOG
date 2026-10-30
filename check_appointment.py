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

# Search for the appointment
# The name in the screenshot is "GRM-7: Bella (2026-02-11)"
# Let's search by name ilike 'GRM-7'
ids = models.execute_kw(db, uid, password, 'grooming.appointment', 'search', [[['name', 'ilike', 'GRM-7']]])

if ids:
    print(f"Found Appointment ID: {ids}")
    # Read fields
    data = models.execute_kw(db, uid, password, 'grooming.appointment', 'read', [ids, ['name', 'state', 'sale_order_id', 'partner_id']])
    for record in data:
        print(f"Name: {record['name']}")
        print(f"State: {record['state']}")
        print(f"Sales Order: {record['sale_order_id']}") # Should be (id, name) or False
        print(f"Customer: {record['partner_id']}")
else:
    print("Appointment not found")
