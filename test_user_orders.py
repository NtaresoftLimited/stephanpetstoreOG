import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "wpo,,CWc2VH^PZ"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

script = """
import logging
logging.disable(logging.CRITICAL)

user_11 = env['res.users'].browse(11)
print(f"User 11: {user_11.name}")

# Check orders visible to user 11
orders_as_user11 = env['pos.order'].with_user(user_11).search([])
print(f"Orders visible to User 11 currently: {len(orders_as_user11)}")
if orders_as_user11:
    print(f"  Earliest order date: {min(orders_as_user11.mapped('date_order'))}")
    print(f"  Latest order date: {max(orders_as_user11.mapped('date_order'))}")

# Test updating domain on rule 926
rule_926 = env['ir.rule'].browse(926)
print(f"Current domain on rule 926: {rule_926.domain_force}")

# Also check rule 764
rule_764 = env['ir.rule'].browse(764)
print(f"Current domain on rule 764: {rule_764.domain_force}")
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/test_rule_eval.py", "w") as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su -s /bin/bash odoo -c '/opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo/odoo_stephans.conf -d Stephans < /tmp/test_rule_eval.py'")
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
