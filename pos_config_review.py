#!/usr/bin/env python3
import paramiko
import sys

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

script = """
import logging
logging.disable(logging.CRITICAL)

try:
    print("--- Stock Check and POS Config Review ---")
    all_quants = env['stock.quant'].search([('product_id', '=', 2811)])
    for q in all_quants:
        print(f"Product: {q.product_id.display_name} | Location: {q.location_id.complete_name} (ID: {q.location_id.id}) | Qty: {q.quantity}")

    # Check which POS config the user is likely using
    print("\\n--- Current POS Configurations ---")
    configs = env['pos.config'].search([])
    for c in configs:
        print(f"ID: {c.id} | Name: {c.name} | Location ID: {c.picking_type_id.default_location_src_id.id}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/pos_config_review.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/pos_config_review.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
