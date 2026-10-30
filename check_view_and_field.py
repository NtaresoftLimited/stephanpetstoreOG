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
    print("--- Checking View Status ---")
    view = env['ir.ui.view'].search([
        ('name', '=', 'pos.config.allowed_users.view'),
        ('model', '=', 'pos.config')
    ])
    if view:
        print(f"View ID: {view.id} | Active: {view.active} | Inherit ID: {view.inherit_id.name}")
        print("Arch:")
        print(view.arch)
    else:
        print("View 'pos.config.allowed_users.view' not found!")

    print("\\n--- Confirming Field Status ---")
    field = env['ir.model.fields'].search([
        ('model', '=', 'pos.config'),
        ('name', '=', 'x_allowed_users')
    ])
    if field:
        print(f"Field ID: {field.id} | Name: {field.name} | State: {field.state}")
    else:
        print("Field 'x_allowed_users' not found!")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/check_view_and_field.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/check_view_and_field.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
