import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

print("Stopping service...")
ssh.exec_command('systemctl stop odoo-stephans')

cmd = "sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo/odoo_stephans.conf -i custom_pos_reports -d Stephans --stop-after-init --no-http"
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=180)
exit_code = stdout.channel.recv_exit_status()

print("Exit:", exit_code)
# Get the tail of the log instead of stderr since stderr is empty
cmd2 = "tail -n 100 /var/log/odoo/odoo-server.log"
stdin2, stdout2, stderr2 = ssh.exec_command(cmd2)
print("LOG:", stdout2.read().decode())

ssh.exec_command('systemctl start odoo-stephans')
