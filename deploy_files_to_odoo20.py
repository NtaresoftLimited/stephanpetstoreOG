import os, re, sys
import paramiko

ROOT = r"D:\CODEX\STEPHANS OG\stephans-pet-app"
ref = open(os.path.join(ROOT, "scratch", "deploy_all_and_verify.py"), encoding="utf-8").read()
PASSWORD = re.search(r"PASSWORD\s*=\s*['\"]([^'\"]+)", ref).group(1)

FILES_TO_DEPLOY = [
    "custom_pos_reports/models/account_payment_register.py",
    "custom_pos_reports/models/pos_payment_inherit.py",
    "custom_pos_reports/models/sale_order_payment_wizard.py",
    "grooming/controllers/portal.py",
    "grooming/models/grooming.py",
    "grooming/views/grooming_views.xml",
    "grooming/views/portal_templates.xml",
    "stephans_wallet_rewards/views/portal_templates.xml",
    "stephans_website_theme/controllers/grooming.py",
    "stephans_website_theme/controllers/pages.py",
]

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect("166.1.227.63", username="root", password=PASSWORD, timeout=30)
sftp = ssh.open_sftp()

REMOTE_BASE = "/opt/odoo/odoo20-addons"

for rel in FILES_TO_DEPLOY:
    local_path = os.path.join(ROOT, rel.replace('/', os.sep))
    remote_path = f"{REMOTE_BASE}/{rel}"
    print(f"Uploading {rel} -> {remote_path}...")
    sftp.put(local_path, remote_path)

sftp.close()
print("All files uploaded successfully.")

# Set ownership
cmd_chown = f"chown -R odoo:odoo {REMOTE_BASE}/grooming {REMOTE_BASE}/stephans_wallet_rewards {REMOTE_BASE}/stephans_website_theme {REMOTE_BASE}/custom_pos_reports"
_, out, err = ssh.exec_command(cmd_chown)
print("chown output:", out.read().decode())

# Upgrade modules on stephans_odoo20
cmd_upgrade = "su - odoo -s /bin/bash -c '/opt/odoo/venv-odoo20/bin/python3 /opt/odoo/odoo20-community/odoo-bin -c /etc/odoo/odoo20_stephans.conf -d stephans_odoo20 -u grooming,stephans_wallet_rewards,stephans_website_theme,custom_pos_reports --stop-after-init'"
print("Running module upgrade on Odoo 20...")
_, out, err = ssh.exec_command(cmd_upgrade, timeout=300)
out_text = out.read().decode("utf-8", "replace")
err_text = err.read().decode("utf-8", "replace")
print("Upgrade done.")
if "ERROR" in err_text or "CRITICAL" in err_text:
    print("ERRORS in upgrade:", err_text[-2000:])
else:
    print("Upgrade logs clean.")

# Restart odoo20-staging service
print("Restarting odoo20-staging.service...")
_, out, err = ssh.exec_command("systemctl restart odoo20-staging.service")
print("Restart output:", out.read().decode())

# Verify status
_, out, err = ssh.exec_command("systemctl is-active odoo20-staging.service")
status = out.read().decode().strip()
print("odoo20-staging.service status:", status)

ssh.close()
