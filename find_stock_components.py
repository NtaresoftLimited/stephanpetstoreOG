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
        ("Searching for qty_available in XML", "grep -rn 'qty_available' /opt/odoo/custom-addons/wise_pos_stock/static/src/ --include='*.xml'"),
        ("Searching for ProductConfiguratorPopup", "find /opt/odoo/odoo-server/odoo/addons/point_of_sale/static/src/ -name '*ProductConfiguratorPopup*'"),
    ]

    for name, cmd in commands:
        print(f"\n>>> {name}")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        print(out if out else "(no results)")

    client.close()

if __name__ == "__main__":
    main()
