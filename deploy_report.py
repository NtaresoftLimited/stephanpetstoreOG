import paramiko

def run():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

    sftp = ssh.open_sftp()
    
    local_dir = r"D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports"
    remote_dir = "/opt/odoo/custom-addons/custom_pos_reports"
    
    try:
        sftp.mkdir(f"{remote_dir}/data")
    except Exception:
        pass
        
    files_to_upload = [
        ("__manifest__.py", "__manifest__.py"),
        ("wizard/pos_details.py", "wizard/pos_details.py"),
        ("views/pos_details_views.xml", "views/pos_details_views.xml"),
        ("data/cron.xml", "data/cron.xml")
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
