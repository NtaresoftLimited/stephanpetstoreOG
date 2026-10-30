import paramiko
import os

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "wpo,,CWc2VH^PZ"

files_to_sync = [
    ("grooming/models/stock_picking.py", "/opt/odoo/custom-addons/grooming/models/stock_picking.py"),
    ("grooming/models/stock_request.py", "/opt/odoo/custom-addons/grooming/models/stock_request.py"),
    ("grooming/models/product_template.py", "/opt/odoo/custom-addons/grooming/models/product_template.py"),
    ("grooming/static/src/js/request_stock_popup.js", "/opt/odoo/custom-addons/grooming/static/src/js/request_stock_popup.js"),
    ("grooming/static/src/js/replenishment_request_popup.js", "/opt/odoo/custom-addons/grooming/static/src/js/replenishment_request_popup.js"),
    ("grooming/static/src/xml/request_stock_popup.xml", "/opt/odoo/custom-addons/grooming/static/src/xml/request_stock_popup.xml"),
    ("grooming/static/src/xml/replenishment_request_popup.xml", "/opt/odoo/custom-addons/grooming/static/src/xml/replenishment_request_popup.xml"),
    ("custom_pos_reports/security/pos_security.xml", "/opt/odoo/custom-addons/custom_pos_reports/security/pos_security.xml"),
    ("custom_pos_reports/views/pos_order_view.xml", "/opt/odoo/custom-addons/custom_pos_reports/views/pos_order_view.xml"),
]

print("Connecting to SSH...")
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

sftp = ssh.open_sftp()
for local_rel, remote_path in files_to_sync:
    local_path = os.path.join(r"d:\CODEX\STEPHANS OG\stephans-pet-app", local_rel.replace("/", os.sep))
    print(f"Uploading {local_path} -> {remote_path}...")
    sftp.put(local_path, remote_path)
sftp.close()

print("Setting file ownership to odoo:odoo...")
ssh.exec_command("chown -R odoo:odoo /opt/odoo/custom-addons/grooming /opt/odoo/custom-addons/custom_pos_reports")

print("Upgrading modules grooming and custom_pos_reports...")
stdin, stdout, stderr = ssh.exec_command("su -s /bin/bash odoo -c '/opt/odoo/odoo-server/odoo-bin -c /etc/odoo/odoo_stephans.conf -d Stephans -u grooming,custom_pos_reports --stop-after-init'")
exit_status = stdout.channel.recv_exit_status()
print(f"Upgrade exit status: {exit_status}")
out = stdout.read().decode()
err = stderr.read().decode()
if exit_status != 0:
    print("UPGRADE ERROR:")
    print(err[-2000:])
else:
    print("Upgrade successful!")

print("Restarting odoo-stephans.service...")
ssh.exec_command("systemctl restart odoo-stephans")

import time
time.sleep(3)

stdin, stdout, stderr = ssh.exec_command("systemctl is-active odoo-stephans")
print("Service status:", stdout.read().decode().strip())

ssh.close()
