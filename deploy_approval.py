import paramiko

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='kz@j8PbU77r9GZ')
sftp = ssh.open_sftp()

files = [
    (r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py", "/opt/odoo/custom-addons/grooming/models/stock_picking.py"),
    (r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_request.py", "/opt/odoo/custom-addons/grooming/models/stock_request.py"),
    (r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\views\stock_request_views.xml", "/opt/odoo/custom-addons/grooming/views/stock_request_views.xml"),
]

for loc, rem in files:
    print(f"Uploading {loc}...")
    sftp.put(loc, rem)

sftp.close()

print("Stopping Odoo...")
ssh.exec_command("systemctl stop odoo-stephans")

print("Upgrading module...")
cmd = "sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo/odoo_stephans.conf -u grooming -d Stephans --stop-after-init --no-http"
stdin, stdout, stderr = ssh.exec_command(cmd, timeout=180)
exit_code = stdout.channel.recv_exit_status()
print(f"Upgrade completed with code: {exit_code}")
print(stderr.read().decode())

print("Starting Odoo...")
ssh.exec_command("systemctl start odoo-stephans")
ssh.close()
print("Done!")
