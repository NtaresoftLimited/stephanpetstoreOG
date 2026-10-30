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
    print("--- Searching for Dog Rope Toy L ---")
    products = env['product.template'].search([('name', 'ilike', 'Dog Rope Toy L')])
    for t in products:
        print(f"Name: {t.name} (ID: {t.id}) | Qty: {t.qty_available} | POS Category: {t.pos_categ_ids.mapped('name')}")
        for v in t.product_variant_ids:
            print(f"  Variant: {v.display_name} (ID: {v.id}) | Qty: {v.qty_available}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/check_rope_l.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/check_rope_l.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
