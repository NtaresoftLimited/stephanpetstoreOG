import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')

print("=== Check ir_asset for grooming replenishment ===")
stdin, stdout, stderr = ssh.exec_command(
    "sudo -u odoo psql Stephans -c \"SELECT name, bundle FROM ir_asset WHERE name LIKE '%replenishment%';\""
)
print(stdout.read().decode())
print(stderr.read().decode())

print("=== Verify Odoo-stephans is running ===")
stdin, stdout, stderr = ssh.exec_command('systemctl is-active odoo-stephans')
print("Status:", stdout.read().decode().strip())

print("=== Check last log lines ===")
stdin, stdout, stderr = ssh.exec_command('tail -n 20 /var/log/odoo/odoo-stephans.log')
print(stdout.read().decode())

ssh.close()
