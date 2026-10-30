#!/usr/bin/env python3
import os

start_dir = "/opt/odoo/odoo-server/odoo/addons/point_of_sale/static/src/app/screens/receipt_screen/receipt/"
print(f"Listing {start_dir}...")

try:
    for root, dirs, files in os.walk(start_dir):
        for f in files:
            print(os.path.join(root, f))
except Exception as e:
    print(f"Error: {e}")
