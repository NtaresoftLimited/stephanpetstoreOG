import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

script = """
import sys
from odoo import api, SUPERUSER_ID
env = api.Environment(env.cr, SUPERUSER_ID, {})

picking = env['stock.picking']
print("Methods on stock.picking:")
for d in dir(picking):
    if 'whatsapp' in d.lower() or 'wa' in d.lower():
        print(d)
        
print("Actions containing whatsapp:")
actions = env['ir.actions.act_window'].search([('name', 'ilike', 'whatsapp')])
for a in actions:
    print(a.name, a.res_model)
"""

with ssh.open_sftp() as sftp:
    with sftp.file('/tmp/get_wa.py', 'w') as f:
        f.write(script)

cmd = "sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell -c /etc/odoo/odoo_stephans.conf -d Stephans < /tmp/get_wa.py"
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
ssh.close()
