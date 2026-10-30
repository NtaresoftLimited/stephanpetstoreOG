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
    product_pink = env['product.product'].browse(2811)
    loc_masaki = env['stock.location'].browse(8) # MASAK/Stock
    loc_mikoc = env['stock.location'].browse(32) # MIKOC/Stock
    
    print(f"Transferring 2 units of {product_pink.display_name} from Masaki to Mikocheni for testing...")
    
    # Simple inventory adjustment to simulate a transfer or just add stock to Mikoc
    # We'll just add 2 to Mikoc and remove 2 from Masaki to keep it balanced
    
    env['stock.quant'].with_context(inventory_mode=True).create({
        'product_id': product_pink.id,
        'location_id': loc_mikoc.id,
        'inventory_quantity': 2.0,
    }).action_apply_inventory()
    
    env['stock.quant'].with_context(inventory_mode=True).create({
        'product_id': product_pink.id,
        'location_id': loc_masaki.id,
        'inventory_quantity': 2.0, # Reduced from 4
    }).action_apply_inventory()
    
    print("Success. Mikocheni now has 2.0 units of Dog Rope (Pink).")
    
except Exception as e:
    print(f"Error: {e}")
    env.cr.rollback()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/transfer_dog_rope.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/transfer_dog_rope.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
