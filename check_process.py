#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Deep Process Check on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # 1. Process List
    print("\n>>> PS AUX (Odoo):")
    stdin, stdout, stderr = client.exec_command("ps aux | grep odoo")
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # 2. Netstat
    print("\n>>> Netstat (Port 8069):")
    stdin, stdout, stderr = client.exec_command("netstat -tulnp | grep 8069")
    print(stdout.read().decode('utf-8', errors='replace'))

    # 3. SS (Alternative)
    print("\n>>> SS (Port 8069):")
    stdin, stdout, stderr = client.exec_command("ss -tulnp | grep 8069")
    print(stdout.read().decode('utf-8', errors='replace'))

    client.close()

if __name__ == "__main__":
    main()
