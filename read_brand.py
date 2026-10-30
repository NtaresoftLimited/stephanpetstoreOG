import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

stdin, stdout, stderr = ssh.exec_command('cat /opt/odoo/custom-addons/custom_pos_reports/models/brand.py')
print(stdout.read().decode())
ssh.close()
