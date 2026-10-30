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

    # Search for titles in XML files that might be the variant popup
    cmd = "grep -rn 'Attributes' /opt/odoo/odoo-server/odoo/addons/point_of_sale/static/src/app/ --include='*.xml' | head -20"
    stdin, stdout, stderr = client.exec_command(cmd)
    print(">>> Matches for 'Attributes' in XML:")
    print(stdout.read().decode('utf-8', errors='replace'))

    # List components in generic_components
    cmd = "ls /opt/odoo/odoo-server/odoo/addons/point_of_sale/static/src/app/generic_components/"
    stdin, stdout, stderr = client.exec_command(cmd)
    print("\n>>> generic_components:")
    print(stdout.read().decode('utf-8', errors='replace'))

    client.close()

if __name__ == "__main__":
    main()
