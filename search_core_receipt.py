#!/usr/bin/env python3
import paramiko
HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD)

cmds = [
    # Find where taxTotals is computed for POS receipts
    "grep -rn 'tax_totals\\|taxTotals\\|get_tax_totals' /opt/odoo/odoo-server/addons/point_of_sale/static/src/ 2>/dev/null | head -30",
    # Find the standard receipt XML
    "cat /opt/odoo/odoo-server/addons/point_of_sale/static/src/app/screens/receipt_screen/receipt/order_receipt.xml 2>/dev/null | head -120",
    # Check how the total amount is rendered in core
    "grep -n 'label_total\\|amount_total\\|formatCurrency' /opt/odoo/odoo-server/addons/point_of_sale/static/src/app/screens/receipt_screen/receipt/order_receipt.xml 2>/dev/null | head -20",
]
for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    print("===")
client.close()
