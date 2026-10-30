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
    print("--- Searching for Dog Rope Variants and Stock ---")
    
    # Search for product templates with name 'Dog Rope'
    templates = env['product.template'].search([('name', 'ilike', 'Dog Rope')])
    for t in templates:
        print(f"Template ID: {t.id} | Name: {t.name} | Variants Count: {len(t.product_variant_ids)} | Total Stock: {t.qty_available}")
        for v in t.product_variant_ids:
            # Check stock in the internal locations
            print(f"  Variant ID: {v.id} | Display Name: {v.display_name} | Stock: {v.qty_available}")
            
    # Check specifically what wise_get_product_info_pos returns
    location_id = 12 # Default internal location or should I check POS config?
    # Let's find Masaki POS location
    pos_masaki = env['pos.config'].browse(5)
    location = pos_masaki.picking_type_id.default_location_src_id
    print(f"\\nMasaki POS Location: {location.name} (ID: {location.id})")
    
    variant_ids = templates.mapped('product_variant_ids').ids
    if variant_ids:
        # We need to find where 'wise_get_product_info_pos' is defined. 
        # It was defined in pos_session.py or product.py? 
        # Previous grep showed it in pos_session.py but it calls it on product.product.
        # It's likely a monkeypatch.
        
        try:
            res = env['product.product'].wise_get_product_info_pos(location.id, variant_ids)
            print(f"wise_get_product_info_pos results: {res}")
        except Exception as e:
            print(f"Error calling wise_get_product_info_pos: {e}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/check_dog_rope.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/check_dog_rope.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
