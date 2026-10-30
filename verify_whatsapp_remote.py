import xmlrpc.client
import sys

url = "http://166.1.227.63:8069"
db = "Stephans"
username = "info@stephanspetstore.co.tz"
password = "Stephan@3202"

try:
    print(f"Connecting to {url}...")
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("Authentication failed")
        sys.exit(1)

    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))
    
    # 1. Check if model exists
    try:
        # Try to search - if model doesn't exist, it throws an error
        ids = models.execute_kw(db, uid, password, 'whatsapp.instance', 'search', [[]])
        print("SUCCESS: whatsapp.instance model found.")
        print(f"Found {len(ids)} instances.")
    except Exception as e:
        print(f"FAILURE: whatsapp.instance model NOT found or error accessing it: {e}")
        sys.exit(1)

    # 2. Check if menu exists
    menus = models.execute_kw(db, uid, password, 'ir.ui.menu', 'search_count', [[['name', '=', 'WhatsApp']]])
    if menus > 0:
        print("SUCCESS: WhatsApp menu found.")
    else:
        print("WARNING: WhatsApp menu NOT found (check user permissions or menu structure).")

except Exception as e:
    print(f"CONNECTION ERROR: {e}")
    sys.exit(1)
