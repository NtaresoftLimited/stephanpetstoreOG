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
    print("--- Detailed Masaki POS Session Audit ---")
    pos_masaki = env['pos.config'].browse(5)
    session = pos_masaki.current_session_id
    if session:
        print(f"Active Session: {session.name} | State: {session.state}")
        # In Odoo 18, check where it gets stock from during the session
        # Is there a specific location on the session?
    else:
        print("No active session for Masaki.")
    
    print(f"\\nMasaki Config Source Location: {pos_masaki.picking_type_id.default_location_src_id.complete_name} (ID: {pos_masaki.picking_type_id.default_location_src_id.id})")
    
    # Check if 'wise_pos_stock' has any specific settings on this pos_config
    fields = [f for f in pos_masaki._fields if 'stock' in f]
    for f in fields:
        print(f"{f}: {getattr(pos_masaki, f)}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/audit_masaki_pos.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/audit_masaki_pos.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
