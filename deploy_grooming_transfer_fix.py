import paramiko
import os

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "wpo,,CWc2VH^PZ"

files_to_upload = [
    (r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\static\src\js\request_stock_popup.js", "/opt/odoo/custom-addons/grooming/static/src/js/request_stock_popup.js"),
    (r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\static\src\js\replenishment_request_popup.js", "/opt/odoo/custom-addons/grooming/static/src/js/replenishment_request_popup.js"),
    (r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\static\src\xml\request_stock_popup.xml", "/opt/odoo/custom-addons/grooming/static/src/xml/request_stock_popup.xml"),
    (r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\static\src\xml\replenishment_request_popup.xml", "/opt/odoo/custom-addons/grooming/static/src/xml/replenishment_request_popup.xml"),
    (r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py", "/opt/odoo/custom-addons/grooming/models/stock_picking.py"),
]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)
sftp = ssh.open_sftp()

for local_path, remote_path in files_to_upload:
    print(f"Uploading {local_path} -> {remote_path}...")
    sftp.put(local_path, remote_path)
    # Fix permissions
    ssh.exec_command(f"chown odoo:odoo {remote_path} && chmod 664 {remote_path}")

sftp.close()
print("All files uploaded successfully!")

# Upgrade grooming module & restart odoo
print("Restarting Odoo service...")
stdin, stdout, stderr = ssh.exec_command("systemctl restart odoo-stephans")
stdout.channel.recv_exit_status()
print("Odoo service restarted!")

# Upgrade grooming module via odoo-bin
print("Upgrading grooming module...")
stdin, stdout, stderr = ssh.exec_command("su - odoo -c '/opt/odoo/odoo-server/odoo-bin -c /etc/odoo.conf -d Stephans -u grooming --stop-after-init'")
exit_status = stdout.channel.recv_exit_status()
print(f"Upgrade exit status: {exit_status}")
print(stdout.read().decode())
print(stderr.read().decode())

ssh.close()
