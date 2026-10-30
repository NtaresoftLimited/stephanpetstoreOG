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

    open_sessions = env['pos.session'].search([
        ('config_id', '=', pos_mikocheni.id),
        ('state', '!=', 'closed')
    ])
    
    if open_sessions:
        print(f"--- Open Sessions for {pos_mikocheni.name} ---")
        for s in open_sessions:
            print(f"Session: {s.name} | State: {s.state} | Opened By: {s.user_id.name}")
    else:
        print(f"No open sessions found for {pos_mikocheni.name}, but Odoo still blocked the update. Checking for Masaki as well just in case.")
        
except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/check_pos_sessions.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/check_pos_sessions.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
