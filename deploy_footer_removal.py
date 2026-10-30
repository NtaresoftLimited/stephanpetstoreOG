
import paramiko
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

LOCAL_FILE = r"d:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\reports\thermal_template.xml"
REMOTE_FILE = "/opt/odoo/custom-addons/custom_pos_reports/reports/thermal_template.xml"

def main():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=300)

    print("\n" + "="*60)
    print("DEPLOYING THERMAL REPORT FOOTER REMOVAL")
    print("="*60)

    # 1. Upload Template
    print(f"\n>> Uploading template to {REMOTE_FILE}...")
    sftp = client.open_sftp()
    try:
        sftp.put(LOCAL_FILE, REMOTE_FILE)
        print("Upload successful.")
    except Exception as e:
        print(f"Upload failed: {e}")
        return

    # 2. Upload Upgrade Script
    print("\n>> Uploading upgrade script to /tmp/upgrade_pos_reports.py...")
    sftp.put("upgrade_pos_reports.py", "/tmp/upgrade_pos_reports.py")
    sftp.close()

    # 3. Run Upgrade Script
    print("\n>> Executing Module Upgrade...")
    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell -c /etc/odoo.conf -d Stephans --no-http --stop-after-init < /tmp/upgrade_pos_reports.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Stream Output
    for line in stdout:
        line = line.strip()
        if line:
            print(line)
            
    # Check Errors
    err_output = stderr.read().decode().strip()
    if err_output:
        print("\nSTDERR:") 
        print(err_output)

    client.close()
    print("\nDeployment Complete.")

if __name__ == "__main__":
    main()
