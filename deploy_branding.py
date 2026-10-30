
import paramiko
import sys
import io
import os

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

LOCAL_XML = r"d:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\reports\thermal_template.xml"
REMOTE_XML = "/opt/odoo/custom-addons/custom_pos_reports/reports/thermal_template.xml"

LOCAL_PY = r"d:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py"
REMOTE_PY = "/opt/odoo/custom-addons/custom_pos_reports/wizard/pos_details.py"

def main():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=300)

    print("\n" + "="*60)
    print("DEPLOYING BRANDING UPDATES")
    print("="*60)

    sftp = client.open_sftp()

    # 1. Upload XML
    print(f"\n>> Uploading XML template to {REMOTE_XML}...")
    try:
        sftp.put(LOCAL_XML, REMOTE_XML)
        print("XML Upload successful.")
    except Exception as e:
        print(f"XML Upload failed: {e}")

    # 2. Upload Python
    print(f"\n>> Uploading Python file to {REMOTE_PY}...")
    try:
        sftp.put(LOCAL_PY, REMOTE_PY)
        print("Python Upload successful.")
    except Exception as e:
        print(f"Python Upload failed: {e}")

    # 3. Upload Upgrade Script (Reuse existing if available, or upload new)
    # We can reuse the same upgrade logic
    print("\n>> Uploading upgrade script to /tmp/upgrade_pos_reports.py...")
    sftp.put("upgrade_pos_reports.py", "/tmp/upgrade_pos_reports.py")
    sftp.close()

    # 4. Run Upgrade Script
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
