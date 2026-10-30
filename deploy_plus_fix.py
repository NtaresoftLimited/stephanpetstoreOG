import paramiko
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('166.1.227.63', username='root', password='wpo,,CWc2VH^PZ')
sftp = ssh.open_sftp()
files = [
    (r"D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py", "/opt/odoo/custom-addons/custom_pos_reports/wizard/pos_details.py"),
    (r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\product_template.py", "/opt/odoo/custom-addons/grooming/models/product_template.py"),
    (r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py", "/opt/odoo/custom-addons/grooming/models/stock_picking.py"),
    (r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\wizard\whatsapp_transfer_wizard.py", "/opt/odoo/custom-addons/grooming/wizard/whatsapp_transfer_wizard.py")
]
for l, r in files:
    print(f"Uploading {l} -> {r}")
    sftp.put(l, r)
sftp.close()
print("Restarting Odoo...")
ssh.exec_command("systemctl restart odoo-stephans")
ssh.close()
print("Done!")
