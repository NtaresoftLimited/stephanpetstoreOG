import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

stdin, stdout, stderr = ssh.exec_command("grep -rn 'search_read' /opt/odoo/odoo-server/odoo/addons/point_of_sale/static/src/ | grep -i 'order' | head -n 20")
print(stdout.read().decode())
ssh.close()
