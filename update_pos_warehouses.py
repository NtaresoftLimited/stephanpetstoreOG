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
    # 1. Update Mikocheni POS (ID: 7) to use Picking Type ID 36 (MIKOC PoS Orders)
    mikocheni_pos = env['pos.config'].browse(7)
    if mikocheni_pos.exists():
        print(f"Updating {mikocheni_pos.name}...")
        mikocheni_pos.sudo().write({'picking_type_id': 36})
        env.cr.commit()
        print("Success: Updated Mikocheni POS to use MIKOC/Stock.")
    else:
        print("Error: Could not find Mikocheni POS with ID 7.")

    # 2. Verify Masaki POS (ID: 5) is using Correct ID 9
    masaki_pos = env['pos.config'].browse(5)
    if masaki_pos.exists():
        print(f"Verifying {masaki_pos.name}...")
        if masaki_pos.picking_type_id.id != 9:
             masaki_pos.sudo().write({'picking_type_id': 9})
             env.cr.commit()
             print("Fixed Masaki POS to use MASAK/Stock.")
        else:
             print("Masaki POS is already correctly linked.")
    
    # Final Review of settings
    print("\\n--- Updated POS-Warehouse Mapping ---")
    pos_configs = env['pos.config'].search([])
    for config in pos_configs:
        pt = config.picking_type_id
        print(f"POS: {config.name} -> WH: {pt.warehouse_id.name if pt else 'None'} ({pt.default_location_src_id.display_name if pt else 'None'})")

except Exception as e:
    print(f"Error during update: {e}")
    env.cr.rollback()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/update_pos_warehouses.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/update_pos_warehouses.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
