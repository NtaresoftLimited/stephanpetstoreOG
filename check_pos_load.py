import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

stdin, stdout, stderr = ssh.exec_command("grep -rn 'get_pos_orders' /opt/odoo/odoo-server/addons/point_of_sale/ || grep -rn 'pos.order' /opt/odoo/odoo-server/addons/point_of_sale/models/pos_session.py | head -n 30")
print(stdout.read().decode())
ssh.close()
