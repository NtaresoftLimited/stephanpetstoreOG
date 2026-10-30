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

    # Search for order_change in the custom receipt XML
    stdin, stdout, stderr = client.exec_command(
        "grep -n 'order_change' /opt/odoo/custom-addons/custom_receipts_for_pos/static/src/xml/order_receipt.xml"
    )
    print(">>> Matches for 'order_change'")
    print(stdout.read().decode('utf-8', errors='replace').strip())

    # Check for other potential 'in' checks on undefined objects
    stdin, stdout, stderr = client.exec_command(
        "grep -n \" in \" /opt/odoo/custom-addons/custom_receipts_for_pos/static/src/xml/order_receipt.xml"
    )
    print("\n>>> All 'in' checks in the template")
    print(stdout.read().decode('utf-8', errors='replace').strip())

    client.close()

if __name__ == "__main__":
    main()
