#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Restoring Temp DB on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=300)
    
    # 1. Drop if exists
    print(">>> Dropping old temp DB...")
    client.exec_command("su - postgres -c \"dropdb Stephans_Temp_Restore\"")
    
    # 2. Create new
    print(">>> Creating new temp DB...")
    client.exec_command("su - postgres -c \"createdb -O odoo Stephans_Temp_Restore\"")
    
    # 3. Restore
    print(">>> Importing dump.sql (this may take time)...")
    cmd = "su - postgres -c \"psql -d Stephans_Temp_Restore -f /tmp/restore_data/dump.sql\""
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Check for errors in last few lines
    out = stdout.read().decode('utf-8', errors='replace')[-500:]
    err = stderr.read().decode('utf-8', errors='replace')[-500:]
    
    print(f"STDOUT (Trail): {out}")
    if err:
        print(f"STDERR (Trail): {err}")

    client.close()

if __name__ == "__main__":
    main()
