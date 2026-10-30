import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')
stdin, stdout, stderr = ssh.exec_command('journalctl -u odoo-stephans -n 500 | grep -i "Traceback" -B 2 -A 5')
print(stdout.read().decode())
ssh.close()
