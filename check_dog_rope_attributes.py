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
    print("--- Detailed Attribute Investigation for Dog Rope ---")
    t = env['product.template'].browse(2583)
    print(f"Template: {t.name} (ID: {t.id})")
    
    for line in t.attribute_line_ids:
        print(f"Attribute: {line.attribute_id.name} | Display Type: {line.attribute_id.display_type} | Create Variant: {line.attribute_id.create_variant}")
        for val in line.value_ids:
            print(f"  Value: {val.name} (ID: {val.id})")

    # Check if POS set to group variants
    # In Odoo 18, this might be in pos.config
    pos_config = env['pos.config'].browse(7) # Mikocheni
    # Check for any settings related to variants
    print(f"\\nPOS Config: {pos_config.name}")
    # Odoo 18 uses 'product_configurator' on the pos_config?
    # Actually, it's usually on the category or the product.
    
    # Check if the variants themselves are 'Available in POS'
    for v in t.product_variant_ids:
        print(f"Variant: {v.display_name} | ID: {v.id} | POS Available: {v.available_in_pos} | Active: {v.active}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/check_dog_rope_attributes.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/check_dog_rope_attributes.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
