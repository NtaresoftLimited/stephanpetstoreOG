import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')
sftp = ssh.open_sftp()
local_file = r"D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py"
remote_file = "/opt/odoo/custom-addons/custom_pos_reports/wizard/pos_details.py"
sftp.put(local_file, remote_file)
sftp.close()
ssh.exec_command("systemctl restart odoo-stephans")
ssh.close()
