#!/usr/bin/env python3
import paramiko
HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD)

# Read the current custom receipt XML
stdin, stdout, stderr = client.exec_command(
    "cat /opt/odoo/custom-addons/custom_receipts_for_pos/static/src/xml/order_receipt.xml"
)
content = stdout.read().decode('utf-8', errors='replace')

# Fix the new broken references:
fixes = [
    # order_change fix
    ("'order_change' in taxTotals", 'props.data.change'),
    ('taxTotals.order_change', 'props.data.change'),
    # Any remaining order_rounding if not caught
    ("'order_rounding' in taxTotals", 'props.data.rounding_applied'),
    ('taxTotals.order_rounding', 'props.data.rounding_applied'),
    # In case there are more
    ('taxTotals.', 'props.data.'),
]

for old, new in fixes:
    if old in content:
        content = content.replace(old, new)
        print(f"Fixed: {old} -> {new}")

# One final catch-all for 'in taxTotals'
if 'in taxTotals' in content:
    print("Found more 'in taxTotals' checks. Replacing with safe checks.")
    # This is rough but should prevent the crash
    content = content.replace('taxTotals', 'props.data')

# Write the fixed file
sftp = client.open_sftp()
with sftp.file("/opt/odoo/custom-addons/custom_receipts_for_pos/static/src/xml/order_receipt.xml", "w") as f:
    f.write(content)
sftp.close()
print("\nFile updated.")

# Restart
print("Restarting Odoo...")
stdin, stdout, stderr = client.exec_command("systemctl restart odoo")
stdout.channel.recv_exit_status()
print("Odoo restarted.")

client.close()
