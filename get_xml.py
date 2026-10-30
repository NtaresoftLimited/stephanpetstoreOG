import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')
cmd = "cat /opt/odoo/odoo-server/addons/stock/views/stock_picking_views.xml"
stdin, stdout, stderr = ssh.exec_command(cmd)
with open("stock_views.xml", "w") as f:
    f.write(stdout.read().decode())
ssh.close()
