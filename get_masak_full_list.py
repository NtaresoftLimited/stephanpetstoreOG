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
    
    moves = env['stock.move.line'].search([
        '|',
        ('location_id', '=', masak_location.id),
        ('location_dest_id', '=', masak_location.id),
        ('date', '>=', today_start)
    ])
    
    print(f"TOTAL_MOVES:{len(moves)}")
    for move in moves:
        # Determine if it's an addition or subtraction to MASAK
        qty = move.qty_done
        if move.location_dest_id.id == masak_location.id:
            direction = "IN"
        else:
            direction = "OUT"
            
        print(f"{move.product_id.display_name}|{qty}|{direction}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/get_masak_full_list.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/get_masak_full_list.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
