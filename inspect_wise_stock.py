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
        ("Listing files in wise_pos_stock", "find /opt/odoo/custom-addons/wise_pos_stock/ -maxdepth 3"),
        ("Searching for stock loading in JS", "grep -rn 'qty_available\\|bi_on_hand' /opt/odoo/custom-addons/wise_pos_stock/static/src/ 2>/dev/null"),
        ("Searching for variant handling in JS", "grep -rn 'product.product\\|variant' /opt/odoo/custom-addons/wise_pos_stock/static/src/ 2>/dev/null"),
        ("Checking Python models for stock logic", "grep -rn 'def ' /opt/odoo/custom-addons/wise_pos_stock/models/ 2>/dev/null"),
    ]

    for name, cmd in commands:
        print(f"\n>>> {name}")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        print(out if out else "(no results)")

    client.close()

if __name__ == "__main__":
    main()
