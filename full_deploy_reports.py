import paramiko
import os

def run():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')
    sftp = ssh.open_sftp()
    
    local_dir = r"D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports"
    remote_dir = "/opt/odoo/custom-addons/custom_pos_reports"
    
    # ensure base remote_dir exists
    try: sftp.mkdir(remote_dir)
    except: pass
    
    # Upload everything recursively
    for root, dirs, files in os.walk(local_dir):
        # Create directories remotely
        for d in dirs:
            if '__pycache__' in d: continue
            remote_path = os.path.join(remote_dir, os.path.relpath(os.path.join(root, d), local_dir)).replace('\\', '/')
            try: sftp.mkdir(remote_path)
            except: pass
            
        # Upload files
        for f in files:
            if f.endswith('.pyc'): continue
            local_file = os.path.join(root, f)
            remote_path = os.path.join(remote_dir, os.path.relpath(local_file, local_dir)).replace('\\', '/')
            sftp.put(local_file, remote_path)
            print(f"Uploaded {local_file}")
            
    sftp.close()
    
    print("Stopping Odoo before upgrade...")
    ssh.exec_command("systemctl stop odoo-stephans")
    
    print("Upgrading module via python shell...")
    cmd = "sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo/odoo_stephans.conf -i custom_pos_reports -d Stephans --stop-after-init --no-http"
    stdin, stdout, stderr = ssh.exec_command(cmd, timeout=180)
    exit_code = stdout.channel.recv_exit_status()
    print(f"Upgrade completed with code: {exit_code}")
    print(stderr.read().decode())
        
    print("Starting Odoo...")
    ssh.exec_command("systemctl start odoo-stephans")
    ssh.close()
    print("Done!")

if __name__ == "__main__":
    run()
