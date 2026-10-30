import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

print("Stopping odoo-stephans...")
ssh.exec_command('systemctl stop odoo-stephans')

print("Installing...")
cmd = 'sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo/odoo_stephans.conf -i custom_pos_reports -d Stephans --stop-after-init --no-http'
# Let's run it directly via ssh without pty so we can read stderr
stdin, stdout, stderr = ssh.exec_command(cmd)

print("STDOUT:", stdout.read().decode())
print("STDERR:", stderr.read().decode())

print("Starting odoo-stephans...")
ssh.exec_command('systemctl start odoo-stephans')
