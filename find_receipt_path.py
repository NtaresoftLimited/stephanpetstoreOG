#!/usr/bin/env python3
import paramiko
HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD)

cmds = [
    "find /opt/odoo/odoo-server/addons/point_of_sale/static/src/ -name 'order_receipt*'",
    "find /opt/odoo/odoo-server/addons/point_of_sale/static/src/ -name '*.xml' -path '*receipt*'",
    "find /opt/odoo/odoo-server/addons/point_of_sale/static/src/ -name '*.js' -path '*receipt*'",
]
for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(f"CMD: {cmd}")
    print(out if out else "(empty)")
    print("---")

# Also check the actual Odoo path structure
stdin, stdout, stderr = client.exec_command("ls -la /opt/odoo/odoo-server/addons/point_of_sale/static/src/app/screens/receipt_screen/receipt/ 2>/dev/null")
out = stdout.read().decode('utf-8', errors='replace').strip()
print("Receipt dir:")
print(out if out else "(not found)")

# Try alternate path
stdin, stdout, stderr = client.exec_command("find /opt/odoo/odoo-server/addons/point_of_sale/static/ -name '*.xml' | head -30")
out = stdout.read().decode('utf-8', errors='replace').strip()
print("\nAll POS XML files:")
print(out)

client.close()
