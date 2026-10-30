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
    pos_configs = env['pos.config'].search([])
    print("--- Detailed POS - Warehouse Mapping ---")
    for config in pos_configs:
        pt = config.picking_type_id
        warehouse = pt.warehouse_id
        print(f"\\nPOS: {config.name}")
        print(f"  Operation Type: {pt.name if pt else 'None'}")
        print(f"  Linked Warehouse: {warehouse.name if warehouse else 'None'}")
        print(f"  Source Location: {pt.default_location_src_id.display_name if pt and pt.default_location_src_id else 'None'}")
        print(f"  wise_pos_stock - Warehouse Mode: {config.stock_warehouse}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/inspect_pos_details.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/inspect_pos_details.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
