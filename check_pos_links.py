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
    print("--- Searching for POS-User links ---")
    
    user_fields = env['res.users']._fields
    for f in user_fields.keys():
        if 'pos' in f.lower() or 'config' in f.lower():
            print(f"res.users field: {f} (Type: {user_fields[f].type})")
            
    pos_config_fields = env['pos.config']._fields
    for f in pos_config_fields.keys():
        if 'user' in f.lower() or 'employee' in f.lower():
            print(f"pos.config field: {f} (Type: {pos_config_fields[f].type})")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/check_pos_links.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/check_pos_links.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
