#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
MODULE_NAME = "wise_pos_stock"
LOCAL_ZIP = r"D:\CODEX\STEPHANS OG\stephans-pet-app\wise_pos_stock.zip"
REMOTE_ZIP = "/tmp/wise_pos_stock.zip"
ADDONS_PATH = "/opt/odoo/custom-addons"

def main():
    print(f"Deploying {MODULE_NAME} to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    sftp = client.open_sftp()

    print(f"\n[1] Uploading module zip...")
    sftp.put(LOCAL_ZIP, REMOTE_ZIP)
    
    commands = [
        ("Cleaning old version", f"rm -rf {ADDONS_PATH}/{MODULE_NAME}"),
        ("Extracting module", f"unzip -o {REMOTE_ZIP} -d {ADDONS_PATH}"),
        ("Fixing permissions", f"chown -R odoo:odoo {ADDONS_PATH}/{MODULE_NAME} && chmod -R 755 {ADDONS_PATH}/{MODULE_NAME}"),
        ("Stopping Odoo", "systemctl stop odoo"),
        ("Installing Module", f"su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo.conf -d Stephans -i {MODULE_NAME} -u {MODULE_NAME} --stop-after-init\""),
        ("Starting Odoo", "systemctl start odoo"),
        ("Verifying Installation", f"su - postgres -c \"psql Stephans -c \\\"SELECT name, state FROM ir_module_module WHERE name='{MODULE_NAME}';\\\"\"")
    ]

    for name, cmd in commands:
        print(f"\n>>> {name}")
        timeout = 300 if "Installing" in name else 30
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        
        if out: print(out)
        if exit_code != 0:
            print(f"Exit Code: {exit_code}")
            if err: print(f"STDERR: {err}")
        elif err and "Installing" in name:
             print(f"Logs: {err[-1000:]}")

    sftp.close()
    client.close()
    
    print("\n" + "="*60)
    print("MODULE INSTALLED!")
    print("="*60)

if __name__ == "__main__":
    main()
