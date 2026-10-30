import paramiko

def run():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

    sftp = ssh.open_sftp()
    
    files_to_upload = [
        (r"D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py", "/opt/odoo/custom-addons/custom_pos_reports/wizard/pos_details.py"),
        (r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\product_template.py", "/opt/odoo/custom-addons/grooming/models/product_template.py"),
    ]
    
    for local_file, remote_file in files_to_upload:
        print(f"Uploading {local_file}...")
        sftp.put(local_file, remote_file)
        
    sftp.close()
    
    print("Restarting Odoo...")
    ssh.exec_command("systemctl restart odoo-stephans")
    
    ssh.close()
    print("Done!")

if __name__ == "__main__":
    run()
