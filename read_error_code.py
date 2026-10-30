import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

stdin, stdout, stderr = ssh.exec_command('sed -n "60,85p" /opt/odoo/custom-addons/product_auto_code/models/product_template.py')
print(stdout.read().decode())
ssh.close()
