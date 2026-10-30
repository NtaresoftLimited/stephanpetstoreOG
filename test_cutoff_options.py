import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "wpo,,CWc2VH^PZ"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

script = """
import logging
import datetime
logging.disable(logging.CRITICAL)

user_11 = env['res.users'].browse(11)

# Test 1: Start of previous week (last Monday to now)
start_prev_week = (datetime.date.today() - datetime.timedelta(days=datetime.date.today().weekday() + 7)).strftime('%Y-%m-%d 00:00:00')
print(f"Start of previous week: {start_prev_week}")

# Test 2: Rolling 14 days
rolling_14 = (datetime.date.today() - datetime.timedelta(days=14)).strftime('%Y-%m-%d 00:00:00')
print(f"Rolling 14 days: {rolling_14}")

# Test 3: max of both (at least 14 days and always covering full previous week)
cutoff = (datetime.date.today() - datetime.timedelta(days=max(14, datetime.date.today().weekday() + 7))).strftime('%Y-%m-%d 00:00:00')
print(f"Cutoff (max 14 or start of last week): {cutoff}")

# Let's count orders matching cutoff
matching_masaki = env['pos.order'].search([('date_order', '>=', cutoff), ('config_id', '=', 5)])
print(f"Orders for Masaki in that period: {len(matching_masaki)}, sum: {sum(matching_masaki.mapped('amount_total')):,.2f}")
"""

sftp = ssh.open_sftp()
with sftp.file("/tmp/test_cutoff.py", "w") as f:
    f.write(script)
sftp.close()

stdin, stdout, stderr = ssh.exec_command("su -s /bin/bash odoo -c '/opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo/odoo_stephans.conf -d Stephans < /tmp/test_cutoff.py'")
print(stdout.read().decode())
print(stderr.read().decode())
ssh.close()
