#!/usr/bin/env python3
import os

paths_to_check = [
    "/opt/odoo/odoo-server/addons",
    "/usr/lib/python3/dist-packages/odoo/addons",
    "/opt/odoo/custom-addons"
]

for p in paths_to_check:
    print(f"Checking {p}...")
    if os.path.exists(p):
        try:
            items = os.listdir(p)
            if "point_of_sale" in items:
                print(f"FOUND point_of_sale in {p}")
                pos_path = os.path.join(p, "point_of_sale")
                # Look for xmls in static/src
                walk_path = os.path.join(pos_path, "static", "src")
                print(f"Walking {walk_path}...")
                for root, dirs, files in os.walk(walk_path):
                    for f in files:
                        if "receipt" in f.lower() and f.endswith(".xml"):
                            print(f"  Receipt XML: {os.path.join(root, f)}")
        except Exception as e:
            print(f"Error listing {p}: {e}")
    else:
        print(f"Path not found: {p}")
