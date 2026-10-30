import os
import zipfile
import paramiko
import sys

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
LOCAL_DIR = "custom_pos_reports"
REMOTE_DIR = "/opt/odoo/custom-addons"
ZIP_NAME = "custom_pos_reports.zip"

def zip_folder(folder_path, output_path):
    print(f"Zipping {folder_path}...")
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(folder_path))
                zipf.write(file_path, arcname)
    print(f"Created {output_path}")

def main():
    # 1. Zip the folder
    if not os.path.exists(LOCAL_DIR):
        print(f"Error: Directory {LOCAL_DIR} not found.")
        return
    
    zip_folder(LOCAL_DIR, ZIP_NAME)
    
    # 2. Upload and Deploy
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    sftp = client.open_sftp()
    
    remote_zip = f"{REMOTE_DIR}/{ZIP_NAME}"
    print(f"Uploading to {remote_zip}...")
    sftp.put(ZIP_NAME, remote_zip)
    sftp.close()
    
    print("Deploying on server...")
    commands = [
        f"apt-get install -y unzip", # Ensure unzip is installed
        f"rm -rf {REMOTE_DIR}/{LOCAL_DIR}", # Remove old
        f"unzip -o {remote_zip} -d {REMOTE_DIR}", # Unzip
        f"rm {remote_zip}", # Cleanup zip
        f"chown -R odoo:odoo {REMOTE_DIR}/{LOCAL_DIR}", # Fix permissions
        f"chmod -R 755 {REMOTE_DIR}/{LOCAL_DIR}",
        "systemctl stop odoo-stephans",
        f"su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo/odoo_stephans.conf -d Stephans -u custom_pos_reports --stop-after-init\"",
        "systemctl start odoo-stephans",
        f"su - postgres -c \"psql Stephans -c \\\"SELECT count(*) FROM ir_model_access WHERE model_id = (SELECT id FROM ir_model WHERE model = 'product.brand');\\\"\"",
        f"su - postgres -c \"psql Stephans -c \\\"SELECT count(*) FROM ir_model WHERE model = 'product.brand';\\\"\"",
        # Cleanup Duplicate Menus
        f"su - postgres -c \"psql Stephans -c \\\"DELETE FROM ir_ui_menu WHERE name = 'Weekly Report' AND id NOT IN (SELECT res_id FROM ir_model_data WHERE module = 'custom_pos_reports' AND name = 'menu_report_pos_weekly');\\\"\"",
        f"su - postgres -c \"psql Stephans -c \\\"DELETE FROM ir_ui_menu WHERE name = 'Sales Details' AND id NOT IN (SELECT res_id FROM ir_model_data WHERE module = 'custom_pos_reports' AND name = 'menu_report_pos_details_user') AND parent_id IS NULL;\\\"\"",
        "ls -F /var/log/odoo/",
        "tail -n 100 /var/log/odoo/odoo-stephans.log"
    ]
    
    for cmd in commands:
        print(f"Exec: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode().strip()
        err = stderr.read().decode().strip()
        
        if out: print(out)
        if exit_code != 0:
            print(f"Error (Exit {exit_code}): {err}")
            # Don't exit immediately, try to finish (e.g. restart service)
        elif err and "odoo-bin" in cmd:
             # Odoo logs to stderr
             print(f"Log: {err}")

    client.close()
    
    # Cleanup local zip
    if os.path.exists(ZIP_NAME):
        os.remove(ZIP_NAME)
        
    print("Deployment and Upgrade Complete.")

if __name__ == "__main__":
    main()
