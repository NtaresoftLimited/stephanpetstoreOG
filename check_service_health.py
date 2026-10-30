#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking Service Health on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # 1. Service Status
    print("\n>>> Systemctl Status Odoo:")
    stdin, stdout, stderr = client.exec_command("systemctl status odoo --no-pager")
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 2. Check Port 8069
    print("\n>>> Checking Port 8069:")
    # lsof might not be installed, trying ss or netstat
    stdin, stdout, stderr = client.exec_command("ss -tuln | grep 8069")
    print(stdout.read().decode('utf-8', errors='replace'))

    # 3. Check Last 50 Logs
    print("\n>>> Last 50 log lines:")
    stdin, stdout, stderr = client.exec_command("tail -n 50 /var/log/odoo/odoo.log")
    print(stdout.read().decode('utf-8', errors='replace'))

    client.close()

if __name__ == "__main__":
    main()
