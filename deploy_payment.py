import paramiko

def run():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

    sftp = ssh.open_sftp()
    local_dir = r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming"
    remote_dir = "/opt/odoo/custom-addons/grooming"
    
    files_to_upload = [
        ("models/account_payment_register.py", "models/account_payment_register.py"),
        ("models/__init__.py", "models/__init__.py"),
        ("views/account_payment_register_views.xml", "views/account_payment_register_views.xml"),
        ("__manifest__.py", "__manifest__.py")
    ]
    
    for local_file, remote_file in files_to_upload:
        try:
            print(f"Uploading {local_file}...")
            sftp.put(f"{local_dir}\\{local_file.replace('/', '\\')}", f"{remote_dir}/{remote_file}")
        except Exception as e:
            print(f"Warning: could not upload {local_file}: {e}")
            
    sftp.close()
    
    print("Stopping Odoo before upgrade...")
    ssh.exec_command("systemctl stop odoo-stephans")
    
    print("Upgrading module via python shell...")
    cmd = "sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo/odoo_stephans.conf -u grooming -d Stephans --stop-after-init --no-http"
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
