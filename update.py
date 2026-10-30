import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')
cmd = "su - odoo -c '/opt/odoo/odoo-server/odoo-bin -c /etc/odoo.conf -u grooming -d Stephans --stop-after-init'"
print('Stopping...')
ssh.exec_command('systemctl stop odoo')
import time
time.sleep(2)
print('Updating...')
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
print(stderr.read().decode())
print('Starting...')
ssh.exec_command('systemctl start odoo')
ssh.close()
