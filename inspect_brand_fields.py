#!/usr/bin/env python3
"""Fetch Bioline brand logo from Odoo and upload to Sanity."""
import xmlrpc.client
import base64
import io
import json

url = "https://erp.stephanspetstore.co.tz"
db = "Stephans"
user = "info@stephanspetstore.co.tz"
password = "Stephan@3202"

common = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/common")
uid = common.authenticate(db, user, password, {})
models = xmlrpc.client.ServerProxy(f"{url}/xmlrpc/2/object")

# Get available fields on product.brand
fields = models.execute_kw(db, uid, password, "product.brand", "fields_get", [], {"attributes": ["string", "type"]})
image_fields = {k: v for k, v in fields.items() if "image" in k.lower() or "logo" in k.lower()}
print("Image/logo fields on product.brand:")
for k, v in image_fields.items():
    print(f"  {k}: {v['string']} ({v['type']})")
