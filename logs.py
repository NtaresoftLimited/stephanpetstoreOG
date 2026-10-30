import paramiko
import time

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')

print("=== CHECK LOGS FOR HOW ODOO NORMALLY STARTS ===")
stdin, stdout, stderr = ssh.exec_command('tail -n 50 /var/log/odoo/odoo.log 2>/dev/null || journalctl -u odoo -n 50 --no-pager')
print(stdout.read().decode())

ssh.close()
