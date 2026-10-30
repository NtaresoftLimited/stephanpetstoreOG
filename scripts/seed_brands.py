#!/usr/bin/env python3
import xmlrpc.client
import sys
import io

# Force UTF-8 output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Odoo configuration
url = "https://erp.stephanspetstore.co.tz"
db = "Stephans"
username = "info@stephanspetstore.co.tz"
password = "Stephan@3202"

try:
    print("Connecting to Odoo...")
    common = xmlrpc.client.ServerProxy('{}/xmlrpc/2/common'.format(url))
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("Authentication failed!")
        exit(1)

    print(f"Authenticated with UID: {uid}")
    models = xmlrpc.client.ServerProxy('{}/xmlrpc/2/object'.format(url))

    # 1. Create Brand "Beeno"
    print("Checking for 'Beeno' brand...")
    brand_ids = models.execute_kw(db, uid, password, 'product.brand', 'search', [[['name', '=', 'Beeno']]])
    
    brand_id = None
    if brand_ids:
        brand_id = brand_ids[0]
        print(f"[OK] 'Beeno' brand exists with ID: {brand_id}")
    else:
        print("Creating 'Beeno' brand...")
        # Optional: Add logo if you have base64 string
        brand_id = models.execute_kw(db, uid, password, 'product.brand', 'create', [{'name': 'Beeno'}])
        print(f"[OK] Created 'Beeno' brand with ID: {brand_id}")

    # 2. Create Product "Bello" linked to Brand
    print("Checking for 'Bello' product...")
    product_ids = models.execute_kw(db, uid, password, 'product.template', 'search', [[['name', '=', 'Bello Product']]])
    
    if product_ids:
        print(f"[OK] 'Bello Product' exists with ID: {product_ids[0]}")
        # Ensure it's linked to the brand
        models.execute_kw(db, uid, password, 'product.template', 'write', [[product_ids[0]], {'brand_id': brand_id}])
        print(f"Updated 'Bello Product' to link to brand ID: {brand_id}")
    else:
        print("Creating 'Bello Product'...")
        product_id = models.execute_kw(db, uid, password, 'product.template', 'create', [{
            'name': 'Bello Product',
            'type': 'consu', # or 'product'
            'list_price': 100.0,
            'brand_id': brand_id,
            
        }])
        print(f"[OK] Created 'Bello Product' with ID: {product_id}")

except Exception as e:
    print(f"An error occurred: {e}")
