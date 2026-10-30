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

    # Global search for the string 'ProductConfigurator'
    cmd = "grep -rn 'ProductConfigurator' /opt/odoo/odoo-server/ 2>/dev/null | head -50"
    stdin, stdout, stderr = client.exec_command(cmd)
    print(">>> Global grep for 'ProductConfigurator':")
    print(stdout.read().decode('utf-8', errors='replace'))

    client.close()

if __name__ == "__main__":
    main()
