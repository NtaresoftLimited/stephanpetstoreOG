import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "wpo,,CWc2VH^PZ"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

stdin, stdout, stderr = ssh.exec_command("grep -rn 'search_paid_order_ids' /opt/odoo/odoo-server/odoo/addons/point_of_sale/ || grep -rn '_get_pos_orders' /opt/odoo/odoo-server/odoo/addons/point_of_sale/ || grep -rn 'search_read' /opt/odoo/odoo-server/odoo/addons/point_of_sale/static/src/app/screens/ticket_screen/")
print(stdout.read().decode())
ssh.close()
