import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "wpo,,CWc2VH^PZ"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

script = """
import logging
from odoo.tools.safe_eval import _BUILTINS, safe_eval
logging.disable(logging.CRITICAL)

rule = env['ir.rule'].browse(926)
eval_context = rule._eval_context()
print("Keys in ir.rule eval_context:")
for k in sorted(eval_context.keys()):
    print(" ", k, type(eval_context[k]))
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/check_eval_ctx.py", "w") as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su -s /bin/bash odoo -c '/opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo/odoo_stephans.conf -d Stephans < /tmp/check_eval_ctx.py'")
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
