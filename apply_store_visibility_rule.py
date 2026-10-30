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
    print("--- Step 1: Verify Jonas M's Employee Assignment ---")
    pos_mikocheni = env['pos.config'].browse(7)
    pos_masaki = env['pos.config'].browse(5)
    
    print(f"Mikocheni basic_employee_ids: {[(e.id, e.name) for e in pos_mikocheni.basic_employee_ids]}")
    print(f"Mikocheni advanced_employee_ids: {[(e.id, e.name) for e in pos_mikocheni.advanced_employee_ids]}")
    print(f"Masaki basic_employee_ids: {[(e.id, e.name) for e in pos_masaki.basic_employee_ids]}")
    print(f"Masaki advanced_employee_ids: {[(e.id, e.name) for e in pos_masaki.advanced_employee_ids]}")

    print("\\n--- Step 2: Create Record Rule ---")
    pos_config_model = env.ref('point_of_sale.model_pos_config')
    pos_user_group = env.ref('point_of_sale.group_pos_user')

    rule_name = 'POS Config: Restricted to Assigned Stores'
    existing = env['ir.rule'].search([('name', '=', rule_name)])
    
    domain = "['|', ('basic_employee_ids.user_id', 'in', [user.id]), ('advanced_employee_ids.user_id', 'in', [user.id])]"
    
    if existing:
        existing.sudo().write({
            'domain_force': domain,
            'active': True,
        })
        print(f"Updated existing rule (ID: {existing.id}).")
    else:
        env['ir.rule'].sudo().create({
            'name': rule_name,
            'model_id': pos_config_model.id,
            'domain_force': domain,
            'groups': [(4, pos_user_group.id)],
            'perm_read': True,
            'perm_write': True,
            'perm_create': True,
            'perm_unlink': True,
        })
        print("Created new rule.")

    # Ensure Manager override exists so admin sees everything
    pos_manager_group = env.ref('point_of_sale.group_pos_manager')
    mgr_rule_name = 'POS Config: Manager All Access'
    mgr_existing = env['ir.rule'].search([('name', '=', mgr_rule_name), ('model_id', '=', pos_config_model.id)])
    if not mgr_existing:
        env['ir.rule'].sudo().create({
            'name': mgr_rule_name,
            'model_id': pos_config_model.id,
            'domain_force': "[(1, '=', 1)]",
            'groups': [(4, pos_manager_group.id)],
            'perm_read': True,
            'perm_write': True,
            'perm_create': True,
            'perm_unlink': True,
        })
        print("Created Manager override rule.")
    else:
        print("Manager override rule already exists.")

    env.cr.commit()
    print("\\nDone. Rules committed.")

except Exception as e:
    print(f"Error: {e}")
    env.cr.rollback()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/apply_store_visibility_rule.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/apply_store_visibility_rule.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    
    # Restart Odoo
    print("\nRestarting Odoo...")
    stdin2, stdout2, stderr2 = client.exec_command("systemctl restart odoo")
    stdout2.channel.recv_exit_status()
    print("Odoo restarted.")
    
    client.close()

if __name__ == "__main__":
    main()
