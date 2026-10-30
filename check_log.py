import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')
stdin, stdout, stderr = ssh.exec_command('grep -rn "stock_request" /var/log/odoo/odoo-server.log | tail -n 20')
print("STDOUT:", stdout.read().decode())
ssh.close()
