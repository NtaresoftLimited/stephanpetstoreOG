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
    print("--- Fixing POS Rule Access Error ---")
    user_rule = env['ir.rule'].search([('name', '=', 'POS User: Own Orders Only')])
    if user_rule:
        print(f"Modifying rule '{user_rule.name}' to remove create/write/unlink restrictions...")
        user_rule.sudo().write({
            'perm_create': False,
            'perm_write': False,
            'perm_unlink': False,
            'perm_read': True,  # Keep read restriction only
        })
        env.cr.commit()
        print("Success: Rule updated. Users can now create orders again.")
    else:
        print("Could not find rule 'POS User: Own Orders Only'")

except Exception as e:
    print(f"Error: {e}")
    env.cr.rollback()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/fix_pos_rule_create.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/fix_pos_rule_create.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
