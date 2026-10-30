import xmlrpc.client
import sys

url = "https://erp.stephanspetstore.co.tz"
db = "Stephans"
username = "info@stephanspetstore.co.tz"
password = "Stephan@3202"

try:
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    
    # check if action_view_invoices is in fields_get or similar (methods are not in fields_get)
    # easiest way is to try to trigger it on a record, or inspect model attributes if we could (we can't via xmlrpc easily)
    # But we can check if we can call it.
    
    # Search for an appointment
    ids = models.execute_kw(db, uid, password, 'grooming.appointment', 'search', [[]], {'limit': 1})
    if ids:
        print(f"Found appointment {ids[0]}")
        try:
            # Try to call the method action_view_invoices
            # If it doesn't exist, it will raise a Fault
            res = models.execute_kw(db, uid, password, 'grooming.appointment', 'action_view_invoices', [ids[0]])
            print("Method action_view_invoices exists and returned:", res)
        except xmlrpc.client.Fault as e:
            print(f"Method call failed (likely missing): {e}")
            
        try:
             # Try action_create_payment
            res = models.execute_kw(db, uid, password, 'grooming.appointment', 'action_create_payment', [ids[0]])
            print("Method action_create_payment exists and returned:", res)
        except xmlrpc.client.Fault as e:
            print(f"Method action_create_payment failed: {e}")

    else:
        print("No appointments found.")

except Exception as e:
    print(f"Connection error: {e}")
