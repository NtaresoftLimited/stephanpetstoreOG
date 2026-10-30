import paramiko
import sys
import os
import time

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

REMOTE_ADDONS_PATH = "/opt/odoo/custom-addons"

def upload_folder(sftp, local_folder, remote_folder):
    """Recursively upload a folder"""
    try:
        try:
            sftp.stat(remote_folder)
        except FileNotFoundError:
            print(f"Creating remote directory: {remote_folder}")
            sftp.mkdir(remote_folder)

        for item in os.listdir(local_folder):
            local_path = os.path.join(local_folder, item)
            remote_path = f"{remote_folder}/{item}"

            if os.path.isfile(local_path):
                print(f"  Uploading {item}...")
                sftp.put(local_path, remote_path)
            elif os.path.isdir(local_path):
                upload_folder(sftp, local_path, remote_path)
    except Exception as e:
        print(f"Failed to upload folder {local_folder}: {e}")
        raise

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
        sftp = client.open_sftp()
        
        # 1. Upload whatsapp_connector
        print(f"\n>>> Uploading whatsapp_connector...")
        local_wa = os.path.join(os.getcwd(), "whatsapp_connector")
        remote_wa = f"{REMOTE_ADDONS_PATH}/whatsapp_connector"
        upload_folder(sftp, local_wa, remote_wa)

        # 2. Upload updated grooming files
        print(f"\n>>> Uploading updated grooming files...")
        local_grooming = os.path.join(os.getcwd(), "grooming")
        remote_grooming = f"{REMOTE_ADDONS_PATH}/grooming"
        upload_folder(sftp, local_grooming, remote_grooming)

        sftp.close()
        
        # 3. Stop Odoo
        print("\n>>> Stopping Odoo Service...")
        client.exec_command("systemctl stop odoo")
        time.sleep(2)
        
        # 4. Update Modules
        print("\n>>> Installing/Upgrading modules (this may take a minute)...")
        # -i whatsapp_connector to install it
        # -u grooming to update it (and pick up the new dependency)
        cmd = "sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo.conf -d Stephans -i whatsapp_connector -u grooming --stop-after-init"
        print(f"Running: {cmd}")
        
        stdin, stdout, stderr = client.exec_command(cmd)
        
        # Wait for finish and capture output
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        
        print("--- Output ---")
        print(out[-1000:] if len(out) > 1000 else out) # Print last 1000 chars
        if err:
            print("--- Errors/Warnings ---")
            print(err[-1000:] if len(err) > 1000 else err)

        # 5. Start Odoo
        print("\n>>> Starting Odoo Service...")
        client.exec_command("systemctl start odoo")
        
        print("\n>>> Done. Server restarted.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
