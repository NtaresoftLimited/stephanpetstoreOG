#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Searching for backups on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=20)
    
    # Check common backup dirs
    cmd = "find /var/lib/odoo -name '*.zip' -o -name '*.dump' | head -n 20"
    stdin, stdout, stderr = client.exec_command(cmd)
    print("\n>>> /var/lib/odoo Backups:")
    print(stdout.read().decode('utf-8', errors='replace'))

    cmd = "find /opt/odoo -name '*.zip' -o -name '*.dump' | head -n 20"
    stdin, stdout, stderr = client.exec_command(cmd)
    print("\n>>> /opt/odoo Backups:")
    print(stdout.read().decode('utf-8', errors='replace'))
    
    cmd = "find /root -name '*.zip' -o -name '*.dump' | head -n 20"
    stdin, stdout, stderr = client.exec_command(cmd)
    print("\n>>> /root Backups:")
    print(stdout.read().decode('utf-8', errors='replace'))

    client.close()

if __name__ == "__main__":
    main()
