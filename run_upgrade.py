import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')
cmd = "sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo/odoo_stephans.conf -u grooming -d Stephans --stop-after-init --no-http > /tmp/upgrade_odoo.log 2>&1"
stdin, stdout, stderr = ssh.exec_command(cmd)
exit_code = stdout.channel.recv_exit_status()
print("Exit code:", exit_code)
ssh.close()
