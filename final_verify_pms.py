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
    pos_masaki = env['pos.config'].browse(5)
    pos_mikocheni = env['pos.config'].browse(7)
    
    print(f"--- Final Comparison ---")
    print(f"Masaki PMs: {[pm.name for pm in pos_masaki.payment_method_ids]}")
    print(f"Mikocheni PMs: {[pm.name for pm in pos_mikocheni.payment_method_ids]}")
    
    # Check if any Mikocheni sessions are open
    all_sessions = env['pos.session'].search([
        ('config_id', '=', pos_mikocheni.id),
        ('state', '!=', 'closed')
    ])
    print(f"Mikocheni Open Sessions: {len(all_sessions)}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/final_verify_pms.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/final_verify_pms.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
