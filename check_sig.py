import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')
cmd = "cat /opt/odoo/odoo-server/odoo/addons/base/models/ir_actions_report.py | grep -A 2 'def _render_qweb_pdf'"
stdin, stdout, stderr = ssh.exec_command(cmd)
print(stdout.read().decode())
