#!/usr/bin/env python3
import paramiko
import sys
import io

# Force UTF-8 for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Debugging {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    except Exception as e:
        print(f"SSH Failed: {e}")
        sys.exit(1)

    # 1. Read Actual Config
    print("\n>>> Content of /etc/odoo.conf:")
    stdin, stdout, stderr = client.exec_command("cat /etc/odoo.conf")
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 2. Check Journal Logs (since logfile might not be set)
    print("\n>>> Odoo Service Logs (Last 50 lines):")
    stdin, stdout, stderr = client.exec_command("journalctl -u odoo --no-pager -n 50")
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 3. Check Directory Permissions we touched
    print("\n>>> Checking Addons Permissions:")
    stdin, stdout, stderr = client.exec_command("ls -ld /usr/lib/python3/dist-packages/odoo/addons/ /opt/odoo/odoo-server/addons/")
    print(stdout.read().decode('utf-8', errors='replace'))

    client.close()

if __name__ == "__main__":
    main()
