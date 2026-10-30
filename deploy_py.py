import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')
sftp = ssh.open_sftp()

local_py = r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py"
remote_py = "/opt/odoo/custom-addons/grooming/models/stock_picking.py"

print("Uploading stock_picking.py...")
sftp.put(local_py, remote_py)
sftp.close()

print("Restarting Odoo...")
ssh.exec_command("systemctl restart odoo-stephans")
ssh.close()
print("Done!")
