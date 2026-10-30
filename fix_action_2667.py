#!/usr/bin/env python3
"""Fix Odoo action 2667 - view_mode has tree but no tree view exists."""
import xmlrpc.client

url = "https://erp.stephanspetstore.co.tz"
db = "Stephans"
user = "info@stephanspetstore.co.tz"
password = "Stephan@3202"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, user, password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# The action: Brands on product.brand, view_mode: tree,form
# No tree view exists -> replace 'tree' with 'list' (Odoo 17+ uses 'list', not 'tree')
print("Fixing action 2667: changing view_mode from 'tree,form' to 'list,form'...")
result = models.execute_kw(db, uid, password,
    "ir.actions.act_window", "write",
    [[2667], {"view_mode": "list,form"}]
)
print("Done:", result)

# Verify
action = models.execute_kw(db, uid, password,
    "ir.actions.act_window", "read",
    [[2667]],
    {"fields": ["name", "view_mode"]}
)
print("Updated action:", action)
