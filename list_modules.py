#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Listing installed custom modules on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # List ALL installed modules (excluding 'base', 'web', etc is hard in SQL without list, so just dumping name/title)
    # We filter by state='installed'
    cmd = "su - postgres -c \"psql Stephans -c \\\"SELECT name, shortdesc FROM ir_module_module WHERE state = 'installed' ORDER BY name;\\\"\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='replace')
    print(output)
    
    # Check specifically for the old stuck module, regardless of state
    print("\n>>> Checking specific candidates:")
    candidates = ['pos_excel_reports_app_v18', 'custom_pos_reports', 'weekly_report']
    for cand in candidates:
        cmd = f"su - postgres -c \"psql Stephans -c \\\"SELECT name, state FROM ir_module_module WHERE name = '{cand}';\\\"\""
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='replace').strip())

    client.close()

if __name__ == "__main__":
    main()
