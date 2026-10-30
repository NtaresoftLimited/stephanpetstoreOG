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

# Fix the broken references:
# taxTotals.order_total -> props.data.amount_total
# taxTotals.order_rounding -> props.data.rounding_applied
# taxTotals.has_tax_groups -> props.data.tax_details.length > 0
# Also fix related subtotals/tax_groups references

fixes = [
    # Total amount fix
    ('taxTotals.order_total', 'props.data.amount_total'),
    # Rounding fix
    ("'order_rounding' in taxTotals", 'props.data.rounding_applied'),
    ('taxTotals.order_rounding', 'props.data.rounding_applied'),
    # Tax section condition fix
    ('taxTotals and taxTotals.has_tax_groups', 'props.data.tax_details and props.data.tax_details.length > 0'),
    # Subtotals iteration - replace with tax_details
    ('taxTotals.subtotals', 'props.data.tax_details'),
    # Individual tax group references
    ('subtotal.tax_groups', '[]'),
]

for old, new in fixes:
    if old in content:
        content = content.replace(old, new)
        print(f"Fixed: {old} -> {new}")
    else:
        print(f"Not found: {old}")

# Write the fixed file
sftp = client.open_sftp()
with sftp.file("/opt/odoo/custom-addons/custom_receipts_for_pos/static/src/xml/order_receipt.xml", "w") as f:
    f.write(content)
sftp.close()
print("\nFile updated.")

# Fix permissions
client.exec_command("chown odoo:odoo /opt/odoo/custom-addons/custom_receipts_for_pos/static/src/xml/order_receipt.xml")

# Restart
print("Restarting Odoo...")
stdin, stdout, stderr = client.exec_command("systemctl restart odoo")
stdout.channel.recv_exit_status()
print("Odoo restarted.")

client.close()
