#!/usr/bin/env python3
import paramiko
HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASSWORD)

cmds = [
    "ls /opt/odoo/odoo-server/addons/point_of_sale/static/src/",
    "find /opt/odoo/odoo-server/addons/point_of_sale/ -name '*.xml' -not -path '*/data/*' -not -path '*/views/*' -not -path '*/security/*' | head -40",
    "find /opt/odoo/ -path '*/point_of_sale/*receipt*' -name '*.xml' 2>/dev/null | head -10",
    "find /opt/odoo/ -path '*/point_of_sale/*OrderReceipt*' 2>/dev/null | head -10",
]
for cmd in cmds:
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(f"\n>>> {cmd}")
    print(out if out else "(empty)")

client.close()
