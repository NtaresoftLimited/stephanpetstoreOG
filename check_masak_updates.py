#!/usr/bin/env python3
import paramiko
import sys
from datetime import datetime, date

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

script = """
import logging
from datetime import datetime, date, timedelta
logging.disable(logging.CRITICAL)

try:
    # Define "today" as 2026-04-06 based on system time
    today_start = datetime(2026, 4, 6, 0, 0, 0)
    
    # 1. Find the location ID for MASAK/Stock
    masak_location = env['stock.location'].search([('display_name', '=', 'MASAK/Stock')], limit=1)
    if not masak_location:
        print("Error: Could not find MASAK/Stock location.")
    else:
        print(f"--- Stock Updates for {masak_location.display_name} today (2026-04-06) ---")
        
        # 2. Search for stock move lines (actual movements)
        # We look for lines where MASAK/Stock is either source or destination
        moves = env['stock.move.line'].search([
            '|',
            ('location_id', '=', masak_location.id),
            ('location_dest_id', '=', masak_location.id),
            ('date', '>=', today_start)
        ])
        
        if not moves:
            print("No stock movements found for MASAK/Stock today.")
        else:
            print(f"{'Product':<50} | {'Qty':<10} | {'From':<20} | {'To':<20}")
            print("-" * 110)
            for move in moves:
                print(f"{move.product_id.display_name[:50]:<50} | {move.qty_done:<10} | {move.location_id.display_name:<20} | {move.location_dest_id.display_name:<20}")

    # 3. Check current quants in MASAK/Stock just in case
    quants = env['stock.quant'].search([('location_id', '=', masak_location.id), ('inventory_diff_quantity', '!=', 0)])
    if quants:
        print("\\n--- Current Pending Inventory Adjustments in MASAK/Stock ---")
        for q in quants:
             print(f"Product: {q.product_id.name} | Counted: {q.inventory_quantity} | Diff: {q.inventory_diff_quantity}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/check_masak_updates.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/check_masak_updates.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
