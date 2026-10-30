import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

stdin, stdout, stderr = ssh.exec_command('systemctl restart odoo-stephans && journalctl -u odoo-stephans -n 100 -f & sleep 5; kill $!')
print(stdout.read().decode())
ssh.close()
