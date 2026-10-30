#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Searching for report modules on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # List modules with 'report' or 'weekly' in name
    cmd = "su - postgres -c \"psql Stephans -c \\\"SELECT name, state, shortdesc FROM ir_module_module WHERE (name ILIKE '%report%' OR name ILIKE '%weekly%' OR shortdesc ILIKE '%report%' OR shortdesc ILIKE '%weekly%') AND state != 'uninstalled';\\\"\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # Also check the addons directory for folder names
    print("\n>>> Checking /opt/odoo/custom-addons:")
    stdin, stdout, stderr = client.exec_command("ls -F /opt/odoo/custom-addons")
    print(stdout.read().decode('utf-8', errors='replace'))

    client.close()

if __name__ == "__main__":
    main()
