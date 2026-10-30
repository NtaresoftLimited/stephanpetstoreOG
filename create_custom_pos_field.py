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
    print("--- Creating Custom Field x_allowed_users on pos.config ---")
    
    # Check if field exists
    field = env['ir.model.fields'].search([
        ('model', '=', 'pos.config'),
        ('name', '=', 'x_allowed_users')
    ])
    
    if not field:
        # Create fields
        field = env['ir.model.fields'].create({
            'name': 'x_allowed_users',
            'model_id': env.ref('point_of_sale.model_pos_config').id,
            'field_description': 'Allowed Users',
            'ttype': 'many2many',
            'relation': 'res.users',
        })
        print("Success: Field x_allowed_users created.")
    else:
        print("Field x_allowed_users already exists.")

    print("\\n--- Updating pos.config view to show Allowed Users ---")
    # Inherit pos.config view to add the field
    # We'll try to find a place to put it
    view = env['ir.ui.view'].search([
        ('name', '=', 'pos.config.allowed_users.view'),
        ('model', '=', 'pos.config')
    ])
    
    if not view:
        # Create inherited view
        view = env['ir.ui.view'].create({
            'name': 'pos.config.allowed_users.view',
            'model': 'pos.config',
            'inherit_id': env.ref('point_of_sale.pos_config_view_form').id,
            'arch': \"\"\"
                <xpath expr="//sheet" position="inside">
                    <group string="Access Control">
                        <field name="x_allowed_users" widget="many2many_tags"/>
                    </group>
                </xpath>
            \"\"\"
        })
        print("Success: View inherited to show Allowed Users.")
    else:
        print("View already exists.")

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
    with sftp.file("/tmp/create_custom_pos_field.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/create_custom_pos_field.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
