import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')

# First, find which user odoo runs as and how the service is configured
print("=== CHECKING ODOO SERVICE CONFIG ===")
stdin, stdout, stderr = ssh.exec_command('cat /etc/systemd/system/odoo.service 2>/dev/null || cat /lib/systemd/system/odoo.service 2>/dev/null || systemctl cat odoo')
print(stdout.read().decode())
print(stderr.read().decode())

print("=== CHECKING ODOO CONF ===")
stdin, stdout, stderr = ssh.exec_command('cat /etc/odoo.conf 2>/dev/null || cat /etc/odoo/odoo.conf 2>/dev/null')
print(stdout.read().decode())

print("=== CHECKING ODOO USER ===")
stdin, stdout, stderr = ssh.exec_command('id odoo 2>/dev/null && ls -la /opt/odoo/')
print(stdout.read().decode())

ssh.close()
