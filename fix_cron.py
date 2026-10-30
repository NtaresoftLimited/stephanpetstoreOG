import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\data\cron.xml', 'r', encoding='utf-8') as f:
    xml_code = f.read()

xml_code = re.sub(r'<field name="numbercall">-1</field>\s*', '', xml_code)

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\data\cron.xml', 'w', encoding='utf-8') as f:
    f.write(xml_code)

import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

sftp = ssh.open_sftp()
sftp.put(r"D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\data\cron.xml", "/opt/odoo/custom-addons/custom_pos_reports/data/cron.xml")
sftp.close()

script = '''
import traceback
import sys
try:
    mod = env['ir.module.module'].search([('name', '=', 'custom_pos_reports')])
    mod.button_immediate_install()
    print('Success!')
except Exception as e:
    with open('/tmp/err4.log', 'w') as f:
        traceback.print_exc(file=f)
    print('Check /tmp/err4.log')
'''

with ssh.open_sftp() as sftp:
    with sftp.file('/tmp/install6.py', 'w') as f:
        f.write(script)

cmd = 'sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell -c /etc/odoo/odoo_stephans.conf -d Stephans < /tmp/install6.py'
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
cmd = 'cat /tmp/err4.log 2>/dev/null'
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
