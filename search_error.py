import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

stdin, stdout, stderr = ssh.exec_command('grep -rn "You do not have permission to approve products" /opt/odoo/custom-addons/')
print(stdout.read().decode())
ssh.close()
