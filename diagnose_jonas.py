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
    print("--- Diagnosing Jonas M's Access ---")
    
    jonas = env['res.users'].browse(12)
    print(f"User: {jonas.name} (ID: {jonas.id})")
    
    # Check his groups
    pos_user = env.ref('point_of_sale.group_pos_user')
    pos_manager = env.ref('point_of_sale.group_pos_manager')
    
    print(f"Is POS User: {pos_user in jonas.groups_id}")
    print(f"Is POS Manager: {pos_manager in jonas.groups_id}")
    
    # List ALL his POS-related groups
    pos_groups = [g for g in jonas.groups_id if 'pos' in g.full_name.lower() or 'point' in g.full_name.lower()]
    for g in pos_groups:
        print(f"  Group: {g.full_name} (ID: {g.id})")

    print("\\n--- All pos.config Record Rules ---")
    rules = env['ir.rule'].search([('model_id.model', '=', 'pos.config')])
    for r in rules:
        grp_names = [g.full_name for g in r.groups]
        print(f"Rule: {r.name} | Active: {r.active} | Groups: {grp_names}")
        print(f"  Domain: {r.domain_force}")
        print(f"  Read: {r.perm_read} | Write: {r.perm_write} | Create: {r.perm_create} | Unlink: {r.perm_unlink}")

    print("\\n--- Testing Rule with Jonas M ---")
    # Simulate what Jonas sees
    configs_as_jonas = env['pos.config'].with_user(jonas).search([])
    print(f"Jonas sees {len(configs_as_jonas)} POS configs: {[c.name for c in configs_as_jonas]}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/diagnose_jonas.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/diagnose_jonas.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
