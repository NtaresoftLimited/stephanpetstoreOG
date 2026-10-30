#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
MODULE_NAME = "pos_excel_reports_app_v18"

def main():
    print(f"Uninstalling {MODULE_NAME} on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)

    # 1. Find the module path
    print("\n>>> Locating module files...")
    cmd = f"find /opt/odoo /usr/lib/python3/dist-packages/odoo/addons -name {MODULE_NAME} -type d"
    stdin, stdout, stderr = client.exec_command(cmd)
    paths = stdout.read().decode('utf-8', errors='replace').strip().splitlines()
    
    if not paths:
        print("Module files not found on disk!")
    else:
        for path in paths:
            print(f"Found at: {path}")

    # 2. Mark as uninstalled in DB
    print("\n>>> Uninstalling from Database...")
    cmd = f"su - postgres -c \"psql Stephans -c \\\"UPDATE ir_module_module SET state='uninstalled' WHERE name='{MODULE_NAME}';\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace').strip())

    # 3. Delete files
    if paths:
        print(f"\n>>> Deleting module files...")
        for path in paths:
            cmd = f"rm -rf {path}"
            print(f"Removing {path}...")
            client.exec_command(cmd)

    # 4. Restart Odoo
    print("\n>>> Restarting Odoo...")
    client.exec_command("systemctl restart odoo")
    
    # 5. Verify removal
    print("\n>>> Verifying removal from DB...")
    cmd = f"su - postgres -c \"psql Stephans -c \\\"SELECT name, state FROM ir_module_module WHERE name='{MODULE_NAME}';\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace').strip())

    client.close()
    
    print("\n" + "="*60)
    print("MODULE REMOVED!")
    print("="*60)

if __name__ == "__main__":
    main()
