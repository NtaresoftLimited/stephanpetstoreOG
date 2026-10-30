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
    pos_config = env['pos.config'].browse(7) # Mikocheni
    print(f"--- POS Config: {pos_config.name} ---")
    # Check for 'Out of Stock' related fields in Odoo 18 POS
    # Common fields: allow_out_of_stock, limit_categories, etc.
    # In Odoo 18, it's often in the 'pos_config' directly.
    
    # Let's check for any field with 'stock' in it on the pos.config
    fields = [f for f in pos_config._fields if 'stock' in f]
    for f in fields:
        print(f"{f}: {getattr(pos_config, f)}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/check_pos_stock_settings.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/check_pos_stock_settings.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
