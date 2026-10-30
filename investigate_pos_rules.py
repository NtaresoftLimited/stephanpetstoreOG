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
    print("--- POS Order Record Rules ---")
    pos_rules = env['ir.rule'].search([('model_id.model', '=', 'pos.order')])
    for rule in pos_rules:
        groups = [g.name for g in rule.groups]
        print(f"Rule: {rule.name} | Active: {rule.active}")
        print(f"  Domain: {rule.domain_force}")
        print(f"  Groups: {', '.join(groups) if groups else 'Global'}")
        print("-" * 40)
        
    print("\\n--- POS Sessions Record Rules ---")
    session_rules = env['ir.rule'].search([('model_id.model', '=', 'pos.session')])
    for rule in session_rules:
        groups = [g.name for g in rule.groups]
        print(f"Rule: {rule.name} | Active: {rule.active}")
        print(f"  Domain: {rule.domain_force}")
        print(f"  Groups: {', '.join(groups) if groups else 'Global'}")
        print("-" * 40)

    print("\\n--- POS Orders Action (Window Action) ---")
    pos_action = env.ref('point_of_sale.action_pos_pos_form', raise_if_not_found=False)
    if pos_action:
        print(f"Action: {pos_action.name}")
        print(f"  Domain: {pos_action.domain}")
        print(f"  Context: {pos_action.context}")
    else:
        print("Could not find point_of_sale.action_pos_pos_form")
        
    print("\\n--- Custom Filters (ir.filters) for pos.order ---")
    filters = env['ir.filters'].search([('model_id', '=', 'pos.order')])
    for f in filters:
        print(f"Filter: {f.name} | Default: {f.is_default} | Domain: {f.domain} | Context: {f.context}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/investigate_pos_rules.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/investigate_pos_rules.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
