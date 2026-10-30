import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

script = """
import sys
from odoo import api, SUPERUSER_ID
env = api.Environment(env.cr, SUPERUSER_ID, {})
view = env.ref('stock.view_picking_form')
print(view.arch)
"""

with ssh.open_sftp() as sftp:
    with sftp.file('/tmp/get_arch.py', 'w') as f:
        f.write(script)

cmd = "sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell -c /etc/odoo/odoo_stephans.conf -d Stephans < /tmp/get_arch.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
with open("arch.xml", "wb") as f:
    f.write(stdout.read())

ssh.close()
