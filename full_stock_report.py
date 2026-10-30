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
    print("--- FULL STOCK REPORT FOR DOG ROPE ---")
    product_ids = [2811, 2812]
    for pid in product_ids:
        p = env['product.product'].browse(pid)
        print(f"\\nProduct: {p.display_name}")
        quants = env['stock.quant'].search([('product_id', '=', pid)])
        for q in quants:
            if q.quantity != 0:
                print(f"  Location: {q.location_id.complete_name} | Qty: {q.quantity}")
                
    # Check current POS session locations
    print("\\n--- ACTIVE POS CONFIGS ---")
    active_configs = env['pos.config'].search([])
    for c in active_configs:
        print(f"POS: {c.name} | Source Location: {c.picking_type_id.default_location_src_id.complete_name} (ID: {c.picking_type_id.default_location_src_id.id})")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/full_stock_report.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/full_stock_report.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
