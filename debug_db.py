#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking Database Visibility on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    except Exception as e:
        print(f"SSH Failed: {e}")
        sys.exit(1)

    commands = [
        # 1. Config Check
        "cat /etc/odoo.conf",
        
        # 2. Postgres DB List
        "su - postgres -c 'psql -l'",
        
        # 3. Check Table Count in Stephans
        "su - postgres -c \"psql Stephans -c 'SELECT count(*) FROM res_users;'\"",
        
        # 4. Check Odoo Process Details
        "ps aux | grep odoo-bin"
    ]

    for cmd in commands:
        print(f"\n>>> Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='replace').strip())
        err = stderr.read().decode('utf-8', errors='replace').strip()
        if err:
            print(f"STDERR: {err}")

    client.close()

if __name__ == "__main__":
    main()
