#!/usr/bin/env python3
import paramiko
HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD)

cmds = [
    "grep -rn 'amount_total' /opt/odoo/odoo-server/addons/point_of_sale/static/src/app/screens/receipt_screen/ 2>/dev/null | head -20",
    "grep -rn 'taxTotals' /opt/odoo/odoo-server/addons/point_of_sale/static/src/app/screens/receipt_screen/ 2>/dev/null | head -20",
    "grep -rn 'order_total' /opt/odoo/odoo-server/addons/account/static/src/components/tax_totals/ 2>/dev/null | head -10",
]
for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    print("---")
client.close()
