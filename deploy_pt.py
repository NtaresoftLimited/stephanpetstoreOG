import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

sftp = ssh.open_sftp()
sftp.put(r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\product_template.py", "/opt/odoo/custom-addons/grooming/models/product_template.py")
sftp.close()

stdin, stdout, stderr = ssh.exec_command('systemctl restart odoo-stephans')
print(stdout.read().decode())
ssh.close()
