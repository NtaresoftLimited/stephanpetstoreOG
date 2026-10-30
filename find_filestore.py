#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Searching for filestore on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    
    # Check specific probable locations first
    cmd = "ls -R /var/lib/odoo/.local/share/Odoo/filestore || echo 'Not found in default'"
    stdin, stdout, stderr = client.exec_command(cmd)
    print("\n>>> Default Location (/var/lib/odoo...):")
    print(stdout.read().decode('utf-8', errors='replace')[:500]) # Cap output

    cmd = "ls -R /opt/odoo/.local/share/Odoo/filestore || echo 'Not found in opt'"
    stdin, stdout, stderr = client.exec_command(cmd)
    print("\n>>> Opt Location (/opt/odoo...):")
    print(stdout.read().decode('utf-8', errors='replace')[:500])

    client.close()

if __name__ == "__main__":
    main()
