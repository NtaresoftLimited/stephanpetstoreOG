import xmlrpc.client
import ssl
import base64
import os

HOST = "erp.stephanspetstore.co.tz"
DB = "Stephans"
USER = "info@stephanspetstore.co.tz"
PASS = "Stephan@3202"
LOGO_PATH = "StephansEcomercewithAI/public/logo.png"

def main():
    print("Reading logo file...")
    if not os.path.exists(LOGO_PATH):
        print(f"Error: Logo file not found at {LOGO_PATH}")
        return

    with open(LOGO_PATH, "rb") as f:
        logo_bytes = f.read()
        logo_b64 = base64.b64encode(logo_bytes).decode('utf-8')
    
    print(f"Logo size: {len(logo_bytes)} bytes")

    # Connect to Odoo
    url = f"https://{HOST}"
    context = ssl._create_unverified_context()
    
    print("Connecting to Odoo...")
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common', context=context)
    uid = common.authenticate(DB, USER, PASS, {})
    
    if not uid:
        print("Authentication failed!")
        return
        
    print(f"Authenticated as User ID: {uid}")
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object', context=context)
    
    # Update Company Logo (Company ID 1 is usually the main company)
    print("Updating Company Logo...")
    models.execute_kw(DB, uid, PASS, 'res.company', 'write', [[1], {
        'logo': logo_b64
    }])
    
    print("✅ Logo updated successfully for Company ID 1.")

if __name__ == "__main__":
    main()
