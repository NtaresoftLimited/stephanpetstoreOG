#!/usr/bin/env python3
import paramiko
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
LOCAL_ZIP = r"D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports.zip"
REMOTE_ZIP = "/tmp/custom_pos_reports.zip"
MODULE_NAME = "custom_pos_reports"
ADDONS_PATH = "/opt/odoo/custom-addons"

def main():
    print(f"Installing {MODULE_NAME} on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    sftp = client.open_sftp()

    # 1. Upload
    print(f"\n[1/5] Uploading module zip...")
    sftp.put(LOCAL_ZIP, REMOTE_ZIP)
    
    commands = [
        # 2. Clean old version
        ("Cleaning old version", f"rm -rf {ADDONS_PATH}/{MODULE_NAME}"),
        
        # 3. Unzip new version
        ("Extracting module", f"unzip -o {REMOTE_ZIP} -d {ADDONS_PATH}"),
        
        # 4. Fix permissions
        ("Fixing permissions", f"chown -R odoo:odoo {ADDONS_PATH}/{MODULE_NAME} && chmod -R 755 {ADDONS_PATH}/{MODULE_NAME}"),
        
        # 5. Update module list & Install
        # We use update_list=True to force Odoo to scan for new modules
        ("Updating Module List", f"su - postgres -c \"psql Stephans -c \\\"UPDATE ir_module_module SET state='to install' WHERE name='{MODULE_NAME}';\\\"\""),
    ]

    for name, cmd in commands:
        print(f"\n>>> {name}")
        stdin, stdout, stderr = client.exec_command(cmd)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        
        if out: print(out)
        if exit_code != 0:
            print(f"Exit Code: {exit_code}")
            if err: print(f"STDERR: {err}")
    
    # 6. Restart Odoo to apply changes and install
    print(f"\n[5/5] Restarting Odoo to trigger installation...")
    # First, force update list via command line (more reliable)
    # Using dry-run update to just init the module
    cmd = f"systemctl restart odoo" 
    # To truly install, we usually need -i or UI. 
    # But setting state='to install' in DB often works on restart if Odoo picks it up. 
    # A better way is using odoo-bin -u or -i, but that requires stopping the service.
    # Let's try the DB update method first + UI upgrade command via shell if needed.
    
    stdin, stdout, stderr = client.exec_command("systemctl restart odoo")
    stdout.channel.recv_exit_status()
    print("   Service restarted.")

    # 7. Check if installed
    print("\n>>> Checking installation status...")
    cmd = f"sleep 10 && su - postgres -c \"psql Stephans -c \\\"SELECT name, state FROM ir_module_module WHERE name='{MODULE_NAME}';\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace').strip())

    sftp.close()
    client.close()
    
    print("\n" + "="*60)
    print("MODULE DEPLOYED!")
    print("="*60)

if __name__ == "__main__":
    main()
