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

    cmd = "find /opt/odoo/odoo-server/odoo/addons/point_of_sale/static/src/ -name '*ProductConfiguratorPopup*'"
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(">>> ProductConfiguratorPopup files:")
    print(out)

    client.close()

if __name__ == "__main__":
    main()
