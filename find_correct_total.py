#!/usr/bin/env python3
import paramiko
import sys

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    # 1. Find the exact line context around order_total
    print(">>> Lines around order_total reference")
    stdin, stdout, stderr = client.exec_command(
        "grep -n -B3 -A3 'order_total' /opt/odoo/custom-addons/custom_receipts_for_pos/static/src/xml/order_receipt.xml"
    )
    print(stdout.read().decode('utf-8', errors='replace').strip())

    # 2. Check what the standard Odoo 18 receipt uses for the total 
    print("\n>>> Standard Odoo 18 OrderReceipt total reference")
    stdin, stdout, stderr = client.exec_command(
        "grep -n 'amount_total\\|order_total\\|total_with_tax\\|formatted_amount' /opt/odoo/odoo-server/addons/point_of_sale/static/src/app/screens/receipt_screen/receipt/order_receipt.xml 2>/dev/null | head -20"
    )
    print(stdout.read().decode('utf-8', errors='replace').strip())

    # 3. Check taxTotals structure in Odoo 18
    print("\n>>> Odoo 18 taxTotals properties in JS")
    stdin, stdout, stderr = client.exec_command(
        "grep -rn 'order_total\\|amount_total_formatted\\|total_amount' /opt/odoo/odoo-server/addons/point_of_sale/static/src/ 2>/dev/null | grep -i taxtotal | head -10"
    )
    print(stdout.read().decode('utf-8', errors='replace').strip())

    client.close()

if __name__ == "__main__":
    main()
