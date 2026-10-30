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
    print("--- Final Fix: Properly injecting field name ---")
    
    field_name = 'x_pos_allowed_users'
    field_settings = env['ir.model.fields'].search([
        ('model', '=', 'res.config.settings'),
        ('name', '=', field_name)
    ])
    
    if not field_settings:
        env['ir.model.fields'].create({
            'name': field_name,
            'model_id': env.ref('base.model_res_config_settings').id,
            'field_description': 'Allowed Users (POS)',
            'ttype': 'many2many',
            'relation': 'res.users',
            'related': 'pos_config_id.x_allowed_users',
            'readonly': False,
        })
        print(f"Success: Field {field_name} created.")

    view_settings = env['ir.ui.view'].search([
        ('name', '=', 'res.config.settings.pos.allowed.users.view'),
        ('model', '=', 'res.config.settings')
    ])
    
    # We use .format() or concatenate to avoid f-string confusion in the Odoo shell script itself
    arch_content = '<xpath expr="//block[@id=\'pos_payment_section\']" position="before">'
    arch_content += '    <block title="Access Control" id="pos_access_section">'
    arch_content += '        <setting string="Allowed Users" help="Assign users who can see this Point of Sale on their dashboard.">'
    arch_content += '            <field name="' + field_name + '" widget="many2many_tags" placeholder="Select users..."/>'
    arch_content += '        </setting>'
    arch_content += '    </block>'
    arch_content += '</xpath>'

    if view_settings:
        view_settings.sudo().write({'arch': arch_content, 'active': True})
    else:
        env['ir.ui.view'].create({
            'name': 'res.config.settings.pos.allowed.users.view',
            'model': 'res.config.settings',
            'inherit_id': env.ref('point_of_sale.res_config_settings_view_form').id,
            'arch': arch_content
        })
    print("Success: View logic applied.")

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
    with sftp.file("/tmp/fix_settings_view_final_v5.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/fix_settings_view_final_v5.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    
    # Restart
    client.exec_command("systemctl restart odoo")
    client.close()
    print("Odoo restarted.")

if __name__ == "__main__":
    main()
