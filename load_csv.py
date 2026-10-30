import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')
sftp = ssh.open_sftp()
script = """
import sys
import logging
from odoo import api, SUPERUSER_ID
from odoo.tools import convert_file

env = api.Environment(env.cr, SUPERUSER_ID, {})
print("Testing CSV load...")
try:
    convert_file(env.cr, 'grooming', 'security/ir.model.access.csv', {}, mode='update', noupdate=False, kind='data')
    env.cr.commit()
    print("SUCCESS: CSV loaded.")
except Exception as e:
    print("FAILED:", str(e))
"""
with sftp.file('/tmp/load_csv.py', 'w') as f:
    f.write(script)
sftp.close()

cmd = "sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell -c /etc/odoo/odoo_stephans.conf -d Stephans < /tmp/load_csv.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
print("Output:", stdout.read().decode())
print("Error:", stderr.read().decode())
ssh.close()
