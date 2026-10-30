import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')
cmd = "find /opt/odoo/odoo-server/addons -name '*payment_register*'"
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()
