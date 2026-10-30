#!/usr/bin/env python3
import paramiko
import sys
from datetime import datetime

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

script = """
import logging
from datetime import datetime
logging.disable(logging.CRITICAL)

try:
    today_start = datetime(2026, 4, 6, 0, 0, 0)
    masak_location = env['stock.location'].search([('display_name', '=', 'MASAK/Stock')], limit=1)
    mikoc_location = env['stock.location'].search([('display_name', '=', 'MIKOC/Stock')], limit=1)
    
    if not masak_location or not mikoc_location:
         print(f"Error: Could not find locations. MASAK:{bool(masak_location)}, MIKOC:{bool(mikoc_location)}")
         raise Exception("Location mismatch")

    # 1. Find all today's moves in MASAK
    moves = env['stock.move.line'].search([
        '|',
        ('location_id', '=', masak_location.id),
        ('location_dest_id', '=', masak_location.id),
        ('date', '>=', today_start)
    ])
    
    product_net_changes = {}
    for move in moves:
        qty = move.qty_done
        pid = move.product_id.id
        if move.location_dest_id.id == masak_location.id:
            product_net_changes[pid] = product_net_changes.get(pid, 0) + qty
        else:
            product_net_changes[pid] = product_net_changes.get(pid, 0) - qty

    print(f"Products to move: {len(product_net_changes)}")
    
    # 2. Apply adjustments
    for pid, net_qty in product_net_changes.items():
        if net_qty == 0: continue
        
        # Reset Masaki to 0 (Assuming the current quantity equals the net change since we reset yesterday)
        # However, to be safe, we just set inventory_quantity to 0 and apply.
        quant_masak = env['stock.quant'].search([('product_id', '=', pid), ('location_id', '=', masak_location.id)], limit=1)
        if not quant_masak:
            quant_masak = env['stock.quant'].create({'product_id': pid, 'location_id': masak_location.id})
        
        # Capture what was in Masaki to inform Mikocheni
        current_masak_qty = quant_masak.quantity
        
        # Set Masaki to 0
        quant_masak.with_context(inventory_mode=True).inventory_quantity = 0
        quant_masak.with_context(inventory_mode=True).action_apply_inventory()

        # Update Mikocheni
        quant_mikoc = env['stock.quant'].search([('product_id', '=', pid), ('location_id', '=', mikoc_location.id)], limit=1)
        if not quant_mikoc:
            quant_mikoc = env['stock.quant'].create({'product_id': pid, 'location_id': mikoc_location.id})
        
        # We add the Masaki quantity to whatever's in Mikocheni
        quant_mikoc.with_context(inventory_mode=True).inventory_quantity = quant_mikoc.quantity + current_masak_qty
        quant_mikoc.with_context(inventory_mode=True).action_apply_inventory()
        
        print(f"Moved {move.product_id.name[:30]} | Qty: {current_masak_qty}")

    env.cr.commit()
    print("Migration complete and committed.")

except Exception as e:
    print(f"Error during migration: {e}")
    env.cr.rollback()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/migrate_stock_to_mikoc.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/migrate_stock_to_mikoc.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
