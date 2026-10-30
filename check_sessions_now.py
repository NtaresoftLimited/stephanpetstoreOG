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
    pos_mikocheni = env['pos.config'].browse(7)
    if not pos_mikocheni.exists():
        pos_mikocheni = env['pos.config'].search([('name', 'ilike', 'Mikocheni')], limit=1)

    all_sessions = env['pos.session'].search([
        ('config_id', '=', pos_mikocheni.id),
        ('state', '!=', 'closed')
    ])
    
    print(f"--- Open Sessions for {pos_mikocheni.name} ---")
    for s in all_sessions:
        print(f"Session: {s.name} | State: {s.state} | Opened By: {s.user_id.name} | Orders: {len(s.order_ids)}")
        
except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/check_sessions_now.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/check_sessions_now.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
