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
    quants = env['stock.quant'].search([('location_id.usage', '=', 'internal')])
    count = len(quants)
    print(f"Found {count} inventory records across stores.")
    
    # Set inventory_quantity to 0
    quants.with_context(inventory_mode=True).action_set_inventory_quantity_to_zero()
    
    # Apply
    quants.with_context(inventory_mode=True).action_apply_inventory()
    env.cr.commit()
    print("Inventory successfully reset to zero for all stores.")
except Exception as e:
    # If action_set_inventory_quantity_to_zero doesn't exist, we do it manually
    print(f"Method failed or missing: {e}. Trying manual iteration...")
    env.cr.rollback()
    quants = env['stock.quant'].search([('location_id.usage', '=', 'internal')])
    for q in quants:
        q.with_context(inventory_mode=True).inventory_quantity = 0
    quants.with_context(inventory_mode=True).action_apply_inventory()
    env.cr.commit()
    print("Inventory successfully reset to zero (via manual iteration).")
"""

def main():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/reset_inv.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/reset_inv.py\""
    
    print("Running reset script in Odoo shell...")
    stdin, stdout, stderr = client.exec_command(cmd)
    
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()

    if out:
        # Filter out odoo startup logs if any, but since we disabled logging it should be cleaner
        print(out)
    if exit_status != 0:
        print(f"Error (Exit {exit_status}):\n{err}")

    client.close()

if __name__ == "__main__":
    main()
