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
    print("--- User Filters (ir.filters) ---")
    filters = env['ir.filters'].search([('model_id', '=', 'pos.order')])
    for f in filters:
        print(f"ID: {f.id} | Name: {f.name} | Default: {f.is_default} | User: {f.user_id.name} | Action: {f.action_id.name} | Context: {f.context}")

    print("\\n--- POS Groups Check ---")
    user_group = env.ref('point_of_sale.group_pos_user')
    manager_group = env.ref('point_of_sale.group_pos_manager')
    print(f"User Group ID: {user_group.id}")
    print(f"Manager Group ID: {manager_group.id}")

    # Let's check existing custom rules for POS orders
    print("\\n--- Checking all POS Rules ---")
    rules = env['ir.rule'].search([('model_id.model', '=', 'pos.order')])
    for r in rules:
        print(f"Rule {r.id}: {r.name} | Groups: {[g.name for g in r.groups]} | Domain: {r.domain_force}")
        
except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/check_filters_rules.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/check_filters_rules.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
