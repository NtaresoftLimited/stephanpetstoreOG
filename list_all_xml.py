#!/usr/bin/env python3
import os

start_dir = "/opt/odoo/odoo-server/addons/point_of_sale/static/src/"
print(f"Listing XMLs in {start_dir}...")

for root, dirs, files in os.walk(start_dir):
    for f in files:
        if f.endswith('.xml'):
            print(os.path.join(root, f))
