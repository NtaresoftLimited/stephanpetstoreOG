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

    cmds = [
        "find /opt/odoo/odoo-server/addons/point_of_sale/static/src/ -name '*Popup*' | head -20",
        "grep -r 'attributes' /opt/odoo/odoo-server/addons/point_of_sale/static/src/app/screens/ 2>/dev/null | head -20",
    ]

    for cmd in cmds:
        print(f"\n>>> {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        print(out if out else "(no results)")

    client.close()

if __name__ == "__main__":
    main()
