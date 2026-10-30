import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')
sftp = ssh.open_sftp()
script = """
import sys
from odoo import api, SUPERUSER_ID
env = api.Environment(env.cr, SUPERUSER_ID, {})
print("Does grooming.stock.request exist in env?", 'grooming.stock.request' in env)
"""
with sftp.file('/tmp/check_env.py', 'w') as f:
    f.write(script)
sftp.close()

cmd = "sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell -c /etc/odoo/odoo_stephans.conf -d Stephans < /tmp/check_env.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
print("Output:", stdout.read().decode())
print("Error:", stderr.read().decode())
ssh.close()
