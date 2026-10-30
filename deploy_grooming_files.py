import paramiko
import sys
import os

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "kz@j8PbU77r9GZ"
LOCAL_DIR = "grooming"
REMOTE_DIR = "/opt/odoo/custom-addons/grooming"

def upload_dir(sftp, local_dir, remote_dir):
    for root, dirs, files in os.walk(local_dir):
        # Ignore pycache
        if '__pycache__' in root:
            continue
            
        relative_path = os.path.relpath(root, local_dir)
        remote_path = os.path.join(remote_dir, relative_path).replace("\\", "/")
        
        try:
            sftp.stat(remote_path)
        except IOError:
            sftp.mkdir(remote_path)
            
        for file in files:
            local_file = os.path.join(root, file)
            remote_file = os.path.join(remote_path, file).replace("\\", "/")
            print(f"Uploading {local_file} -> {remote_file}")
            sftp.put(local_file, remote_file)

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
        sftp = client.open_sftp()
        
        print("Uploading entire grooming module...")
        upload_dir(sftp, LOCAL_DIR, REMOTE_DIR)
            
        sftp.close()
        
        print("Fixing permissions...")
        client.exec_command(f'sudo chown -R odoo:odoo {REMOTE_DIR}')
        
        print("Stopping Odoo Services...")
        client.exec_command('sudo systemctl stop odoo && sudo systemctl stop odoo-stephans')
        
        print("Upgrading 'grooming' module (applying XML/Product changes)...")
        _, stdout, stderr = client.exec_command('sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo/odoo_stephans.conf -d Stephans -u grooming --stop-after-init')
        out = stdout.read().decode()
        err = stderr.read().decode()
        if err:
            print("Errors/Warnings:")
            print(err)
            
        print("Starting Odoo Services...")
        _, stdout, stderr = client.exec_command('sudo systemctl start odoo && sudo systemctl start odoo-stephans')
        out = stdout.read().decode() # Wait for start
        
        print("Done.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
