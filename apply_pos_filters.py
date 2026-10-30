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
    print("--- 1. Cleaning up User Filters ---")
    bad_filters = env['ir.filters'].search([('model_id', '=', 'pos.order')])
    deleted_count = 0
    for f in bad_filters:
        if 'group_by' in f.context:
            print(f"Deleting filter: {f.name} (User: {f.user_id.name})")
            f.sudo().unlink()
            deleted_count += 1
    print(f"Deleted {deleted_count} custom grouping filters.")

    print("\\n--- 2. Updating Window Action ---")
    pos_action = env.ref('point_of_sale.action_pos_pos_form', raise_if_not_found=False)
    if pos_action:
        # Check if context has 'search_default_group_by_week' string
        context_str = pos_action.context
        if 'search_default_group_by_week' in context_str:
            print(f"Original Context: {context_str}")
            import ast
            try:
                # Safely parse the dict string
                ctx_dict = ast.literal_eval(context_str)
                if 'search_default_group_by_week' in ctx_dict:
                    del ctx_dict['search_default_group_by_week']
                    pos_action.sudo().write({'context': str(ctx_dict)})
                    print(f"New Context: {pos_action.context}")
            except Exception as context_e:
                print(f"Failed to parse context: {context_e}")
        else:
            print("No action update needed.")

    print("\\n--- 3. Creating Record Rules ---")
    pos_user_group = env.ref('point_of_sale.group_pos_user')
    pos_manager_group = env.ref('point_of_sale.group_pos_manager')
    model_pos_order = env.ref('point_of_sale.model_pos_order')

    # Look for existing user rule
    user_rule = env['ir.rule'].search([('name', '=', 'POS User: Own Orders Only')])
    if not user_rule:
        env['ir.rule'].sudo().create({
            'name': 'POS User: Own Orders Only',
            'model_id': model_pos_order.id,
            'domain_force': "[('user_id', '=', user.id)]",
            'groups': [(4, pos_user_group.id)],
            'perm_read': True,
            'perm_write': True,
            'perm_create': True,
            'perm_unlink': True,
        })
        print("Created POS User Personal Orders Rule.")
    else:
        print("POS User Personal Orders Rule already exists.")

    # Look for existing manager rule
    manager_rule = env['ir.rule'].search([('name', '=', 'POS Manager: All Orders')])
    if not manager_rule:
        env['ir.rule'].sudo().create({
            'name': 'POS Manager: All Orders',
            'model_id': model_pos_order.id,
            'domain_force': "[(1, '=', 1)]",
            'groups': [(4, pos_manager_group.id)],
            'perm_read': True,
            'perm_write': True,
            'perm_create': True,
            'perm_unlink': True,
        })
        print("Created POS Manager All Orders Rule.")
    else:
        print("POS Manager All Orders Rule already exists.")

    env.cr.commit()
    print("\\nUpdate completed successfully.")

except Exception as e:
    print(f"Script Error: {e}")
    env.cr.rollback()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/apply_pos_filters.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/apply_pos_filters.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
