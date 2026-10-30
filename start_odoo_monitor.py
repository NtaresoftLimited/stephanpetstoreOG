#!/usr/bin/env python3
import paramiko
import time
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Starting Odoo on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    print(">>> Systemctl Start...")
    client.exec_command("systemctl start odoo")
    
    # Wait 5 seconds
    time.sleep(5)
    
    print("\n>>> Status Check:")
    stdin, stdout, stderr = client.exec_command("systemctl status odoo --no-pager")
    print(stdout.read().decode('utf-8', errors='replace'))
    
    print("\n>>> Port 8069:")
    stdin, stdout, stderr = client.exec_command("ss -tulnp | grep 8069")
    print(stdout.read().decode('utf-8', errors='replace'))

    client.close()

if __name__ == "__main__":
    main()
