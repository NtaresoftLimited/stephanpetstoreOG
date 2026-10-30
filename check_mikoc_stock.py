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
    product_ids = [2811, 2812]
    pos_mikocheni = env['pos.config'].browse(7) # ID 7 is Mikocheni
    loc_mikoc = pos_mikocheni.picking_type_id.default_location_src_id
    
    print(f"Mikocheni Location: {loc_mikoc.complete_name} (ID: {loc_mikoc.id})")
    
    res = env['product.product'].wise_get_product_info_pos(loc_mikoc.id, product_ids)
    print(f"wise_get_product_info_pos results for Mikocheni: {res}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/check_mikoc_stock.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/check_mikoc_stock.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
