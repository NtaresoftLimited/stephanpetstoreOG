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
    print("--- Adding Allowed Users to Settings View ---")
    
    # 1. We need to add a related field to res.config.settings
    # But for simplicity, we first modify the pos.config view to be accessible 
    # where the user is looking.
    
    # The screenshot shows the SETTINGS view (res.config.settings).
    
    view_settings = env['ir.ui.view'].search([
        ('name', '=', 'res.config.settings.pos.allowed.users.view'),
        ('model', '=', 'res.config.settings')
    ])
    
    if not view_settings:
        view_settings = env['ir.ui.view'].create({
            'name': 'res.config.settings.pos.allowed.users.view',
            'model': 'res.config.settings',
            'inherit_id': env.ref('point_of_sale.res_config_settings_view_form').id,
            'arch': \"\"\"
                <xpath expr="//div[@id='pos_interface_section']" position="after">
                    <div class="col-12 col-lg-6 o_setting_box" id="allowed_users_section">
                        <div class="o_setting_left_pane"/>
                        <div class="o_setting_right_pane">
                            <span class="o_form_label">Dashboard Access Control</span>
                            <div class="text-muted">
                                Assign users who can see this Point of Sale on their dashboard.
                            </div>
                            <div class="content-group mt16">
                                <field name="pos_x_allowed_users" widget="many2many_tags" 
                                       context="{'pos_config_id': pos_config_id}"/>
                            </div>
                        </div>
                    </div>
                </xpath>
            \"\"\"
        })
        print("Success: Settings view inherited.")
    
    # 2. We need to make sure res.config.settings has this field related to pos.config's x_allowed_users
    field_settings = env['ir.model.fields'].search([
        ('model', '=', 'res.config.settings'),
        ('name', '=', 'pos_x_allowed_users')
    ])
    
    if not field_settings:
        field_settings = env['ir.model.fields'].create({
            'name': 'pos_x_allowed_users',
            'model_id': env.ref('base.model_res_config_settings').id,
            'field_description': 'Allowed Users (POS)',
            'ttype': 'many2many',
            'relation': 'res.users',
            'related': 'pos_config_id.x_allowed_users',
            'readonly': False,
        })
        print("Success: Related field created in settings.")

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
    with sftp.file("/tmp/add_to_settings_view.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/add_to_settings_view.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    
    # Restart
    client.exec_command("systemctl restart odoo")
    client.close()
    print("Odoo restarted.")

if __name__ == "__main__":
    main()
