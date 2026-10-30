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

    commands = [
        ("Full Receipt XML", "cat /opt/odoo/custom-addons/custom_receipts_for_pos/static/src/xml/order_receipt.xml"),
        ("Check POS config for custom receipt setting", "grep -r 'is_custom_receipt\\|design_receipt' /opt/odoo/custom-addons/custom_receipts_for_pos/models/ 2>/dev/null"),
        ("Receipt designs data", "grep -r 'order_total' /opt/odoo/custom-addons/custom_receipts_for_pos/ 2>/dev/null"),
    ]

    for name, cmd in commands:
        print(f"\n{'='*60}")
        print(f">>> {name}")
        print('='*60)
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        print(out[:3000] if out else "(no results)")

    client.close()

if __name__ == "__main__":
    main()
