import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "wpo,,CWc2VH^PZ"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)
sftp = ssh.open_sftp()

local_file = r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\product_template.py"
remote_file = "/opt/odoo/custom-addons/grooming/models/product_template.py"

print("Uploading product_template.py...")
sftp.put(local_file, remote_file)
sftp.close()

ssh.exec_command(f"chown odoo:odoo {remote_file} && chmod 664 {remote_file}")
print("Uploaded product_template.py successfully!")
ssh.close()
