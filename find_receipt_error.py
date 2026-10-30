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
        ("Listing custom addons", "ls /opt/odoo/custom-addons/"),
        ("Searching for order_total in custom modules", "grep -rl 'order_total' /opt/odoo/custom-addons/ 2>/dev/null"),
        ("Searching for OrderReceipt in custom modules", "grep -rl 'OrderReceipt' /opt/odoo/custom-addons/ 2>/dev/null"),
        ("Searching for receipt templates", "find /opt/odoo/custom-addons/ -name '*.xml' | xargs grep -l 'OrderReceipt' 2>/dev/null"),
    ]

    for name, cmd in commands:
        print(f"\n>>> {name}")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        if out:
            print(out)
        else:
            print("(no results)")

    client.close()

if __name__ == "__main__":
    main()
