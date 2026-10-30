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
    print("--- Detailed Stock Check for Dog Rope in Mikocheni ---")
    pos_mikocheni = env['pos.config'].browse(7) # Mikocheni
    loc_mikoc = pos_mikocheni.picking_type_id.default_location_src_id
    
    t = env['product.template'].browse(2583)
    # Get template qty in Mikocheni
    t_qty = t.with_context(location=loc_mikoc.id).qty_available
    print(f"Template '{t.name}' (ID: {t.id}) Qty in Mikocheni: {t_qty}")
    
    for v in t.product_variant_ids:
        v_qty = v.with_context(location=loc_mikoc.id).qty_available
        print(f"  Variant '{v.display_name}' (ID: {v.id}) Qty in Mikocheni: {v_qty}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/check_mikoc_stock_detailed.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/check_mikoc_stock_detailed.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
