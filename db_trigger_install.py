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
    print(f"Triggering install via DB on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)

    # 1. Update State
    print(">>> Setting state to 'to install'...")
    cmd = "su - postgres -c \"psql Stephans -c \\\"UPDATE ir_module_module SET state='to install' WHERE name='custom_pos_reports';\\\"\""
    client.exec_command(cmd)
    
    # 2. Restart Odoo
    print(">>> Restarting Odoo Service...")
    client.exec_command("systemctl restart odoo")
    
    # 3. Wait and Verify
    print(">>> Waiting for installation (20s)...")
    time.sleep(20)
    
    print("\n>>> Module State Check:")
    cmd = "su - postgres -c \"psql Stephans -c \\\"SELECT name, state FROM ir_module_module WHERE name='custom_pos_reports';\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace').strip())

    client.close()

if __name__ == "__main__":
    main()
