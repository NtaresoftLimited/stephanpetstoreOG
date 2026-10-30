import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
try:
    ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')
    cmd = "grep 'name=\"location_id\"' /opt/odoo/odoo-server/odoo/addons/stock/views/stock_picking_views.xml"
    stdin, stdout, stderr = ssh.exec_command(cmd)
    print("STDOUT:", stdout.read().decode())
    
finally:
    ssh.close()
