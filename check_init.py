import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')
stdin, stdout, stderr = ssh.exec_command('cat /opt/odoo/custom-addons/grooming/models/__init__.py')
print("STDOUT:", stdout.read().decode())
ssh.close()
