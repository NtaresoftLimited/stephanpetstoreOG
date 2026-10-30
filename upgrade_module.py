import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

stdin, stdout, stderr = ssh.exec_command('sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo/odoo_stephans.conf -u custom_pos_reports -d Stephans --stop-after-init')
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
