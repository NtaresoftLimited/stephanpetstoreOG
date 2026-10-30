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
    print("--- Removing conflicting rule ---")
    
    # Delete the old "Allowed Users Only" rule that uses x_allowed_users
    # This rule has ('x_allowed_users', '=', False) which matches everything
    old_rule = env['ir.rule'].search([('name', '=', 'POS Config: Allowed Users Only')])
    if old_rule:
        old_rule.sudo().unlink()
        print(f"Deleted rule: 'POS Config: Allowed Users Only' (ID: {old_rule.id})")
    else:
        print("Old rule not found (already deleted).")

    env.cr.commit()

    # Verify remaining rules
    print("\\n--- Remaining pos.config rules ---")
    rules = env['ir.rule'].search([('model_id.model', '=', 'pos.config')])
    for r in rules:
        grp_names = [g.full_name for g in r.groups]
        print(f"Rule: {r.name} | Active: {r.active} | Groups: {grp_names}")
        print(f"  Domain: {r.domain_force}")

    # Test Jonas again
    print("\\n--- Testing Jonas M visibility ---")
    jonas = env['res.users'].browse(12)
    configs = env['pos.config'].with_user(jonas).search([])
    print(f"Jonas now sees {len(configs)} POS config(s): {[c.name for c in configs]}")

except Exception as e:
    print(f"Error: {e}")
    env.cr.rollback()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/fix_conflicting_rules.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/fix_conflicting_rules.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)

    # Restart
    print("\nRestarting Odoo...")
    stdin2, stdout2, stderr2 = client.exec_command("systemctl restart odoo")
    stdout2.channel.recv_exit_status()
    print("Odoo restarted.")
    
    client.close()

if __name__ == "__main__":
    main()
