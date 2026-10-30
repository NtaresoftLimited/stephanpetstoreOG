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
    print("--- Creating Record Rule for POS Dashboard Access ---")
    
    pos_config_model = env.ref('point_of_sale.model_pos_config')
    pos_user_group = env.ref('point_of_sale.group_pos_user')
    pos_manager_group = env.ref('point_of_sale.group_pos_manager')

    # 1. Access Rule for regular POS Users
    user_rule = env['ir.rule'].search([('name', '=', 'POS Config: Allowed Users Only')])
    if not user_rule:
        user_rule = env['ir.rule'].create({
            'name': 'POS Config: Allowed Users Only',
            'model_id': pos_config_model.id,
            'domain_force': "['|', ('x_allowed_users', '=', False), ('x_allowed_users', 'in', [user.id])]",
            'groups': [(4, pos_user_group.id)],
            'perm_read': True,
            'perm_write': True,
            'perm_create': True,
            'perm_unlink': True,
        })
        print("Success: User restriction rule created.")
    else:
        print("User restriction rule already exists.")

    # 2. Access Rule for Managers (Overrides user rule to see everything)
    manager_rule = env['ir.rule'].search([('name', '=', 'POS Config: Manager All Access')])
    if not manager_rule:
        manager_rule = env['ir.rule'].create({
            'name': 'POS Config: Manager All Access',
            'model_id': pos_config_model.id,
            'domain_force': "[(1, '=', 1)]",
            'groups': [(4, pos_manager_group.id)],
            'perm_read': True,
            'perm_write': True,
            'perm_create': True,
            'perm_unlink': True,
        })
        print("Success: Manager override rule created.")
    else:
        print("Manager override rule already exists.")

    env.cr.commit()
    print("\\n--- Success ---")

except Exception as e:
    print(f"Error: {e}")
    env.cr.rollback()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/create_pos_access_rules.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/create_pos_access_rules.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
