#!/usr/bin/env python3
import paramiko
import sys
import ast

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

script = """
import logging
import ast
logging.disable(logging.CRITICAL)

try:
    pos_action = env.ref('point_of_sale.action_pos_pos_form', raise_if_not_found=False)
    if pos_action:
        context_str = pos_action.context or "{}"
        try:
            ctx_dict = ast.literal_eval(context_str)
        except:
            ctx_dict = {}
        
        ctx_dict['search_default_group_by_week'] = 1
        pos_action.sudo().write({'context': str(ctx_dict)})
        env.cr.commit()
        print(f"Action context restored to: {pos_action.context}")
    else:
        print("Error: Could not find action point_of_sale.action_pos_pos_form")
        
except Exception as e:
    print(f"Error: {e}")
    env.cr.rollback()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/restore_weekly_grouping.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/restore_weekly_grouping.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
