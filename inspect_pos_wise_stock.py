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
    # 1. Get POS Configs and their related wise_pos_stock fields
    # We'll look for fields starting with 'wise_' or related to stock in pos.config
    pos_configs = env['pos.config'].search([])
    print(f"--- POS Configurations ({len(pos_configs)}) ---")
    
    # Get all fields of pos.config to identify wise_pos_stock fields
    all_fields = env['pos.config']._fields.keys()
    wise_fields = [f for f in all_fields if 'wise' in f or 'stock' in f]
    
    for config in pos_configs:
        print(f"\\nPOS: {config.name} (ID: {config.id})")
        print(f"Warehouse: {config.warehouse_id.name if 'warehouse_id' in all_fields and config.warehouse_id else 'Not Set'}")
        for field in wise_fields:
            val = getattr(config, field)
            # If it's a recordset, show name
            if hasattr(val, 'name'):
                val = val.name
            print(f"  {field}: {val}")

    # 2. Check Warehouse structure
    warehouses = env['stock.warehouse'].search([])
    print(f"\\n--- Warehouses ({len(warehouses)}) ---")
    for wh in warehouses:
        print(f"WH: {wh.name} (Code: {wh.code}) -> Lot Stock ID: {wh.lot_stock_id.display_name}")

except Exception as e:
    print(f"Error during inspection: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/inspect_wise_config.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/inspect_wise_config.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
