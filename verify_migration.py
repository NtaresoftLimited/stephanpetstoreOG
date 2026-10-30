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
    masak = env['stock.location'].search([('display_name', '=', 'MASAK/Stock')], limit=1)
    mikoc = env['stock.location'].search([('display_name', '=', 'MIKOC/Stock')], limit=1)
    
    # Check top 5 items from the previous list
    product_ids = [16, 20, 28, 36, 45] # Examples of IDs or names
    # Better: just check any quants > 0 in MASAK (should be 0) and some in MIKOC
    
    masak_quants = env['stock.quant'].search([('location_id', '=', masak.id), ('quantity', '>', 0)])
    mikoc_quants = env['stock.quant'].search([('location_id', '=', mikoc.id), ('quantity', '>', 0)])
    
    print(f"MASAK_ACTIVE_QUANTS:{len(masak_quants)}")
    for q in masak_quants[:10]:
        print(f"MASAK|{q.product_id.name}|{q.quantity}")
        
    print(f"MIKOC_ACTIVE_QUANTS:{len(mikoc_quants)}")
    for q in mikoc_quants[:10]:
        print(f"MIKOC|{q.product_id.name}|{q.quantity}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/verify_migration.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/verify_migration.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
