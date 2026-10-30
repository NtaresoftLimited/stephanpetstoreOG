#!/usr/bin/env python3
try:
    with open('/etc/odoo.conf', 'r') as f:
        print(f.read())
except FileNotFoundError:
    try:
        with open('/etc/odoo/odoo.conf', 'r') as f:
            print(f.read())
    except Exception as e:
        print(f"Error: {e}")
