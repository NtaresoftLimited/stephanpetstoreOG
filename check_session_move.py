import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')

test_script = """
import logging
logging.disable(logging.CRITICAL)

# Check if session_id is readonly on pos.order
order_field = env['pos.order']._fields['session_id']
print('session_id readonly?', order_field.readonly)

payment_field = env['pos.payment']._fields['session_id']
print('payment session_id readonly?', payment_field.readonly)
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/test_session_move.py", "w") as f:
    f.write(test_script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su - odoo -c '/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/test_session_move.py'")
print(stdout.read().decode())
ssh.close()
