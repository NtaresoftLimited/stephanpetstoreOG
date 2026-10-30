#!/usr/bin/env python3
import paramiko
HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD)

# Read the core Odoo 18 receipt template
stdin, stdout, stderr = client.exec_command(
    "cat /opt/odoo/odoo-server/odoo/addons/point_of_sale/static/src/app/screens/receipt_screen/receipt/order_receipt.xml"
)
print(stdout.read().decode('utf-8', errors='replace').strip())

client.close()
