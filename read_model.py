import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')

stdin, stdout, stderr = ssh.exec_command('cat /opt/odoo/custom-addons/grooming/models/stock_request.py 2>/dev/null || echo NOT_FOUND')
content = stdout.read().decode()
print(content[:4000])

ssh.close()
