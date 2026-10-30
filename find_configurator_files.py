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

    # Search for ProductConfigurator related files
    # In Odoo 18, it might be in point_of_sale/static/src/app/generic_components/product_configurator/
    cmd = "grep -rl 'ProductConfigurator' /opt/odoo/odoo-server/addons/point_of_sale/static/src/"
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(">>> Files containing 'ProductConfigurator':")
    print(out[:1000] if out else "(no results)")

    client.close()

if __name__ == "__main__":
    main()
