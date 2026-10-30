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
    print("Step 1: Creating Field")
    field_name = 'x_pos_allowed_users'
    f = env['ir.model.fields'].search([('model', '=', 'res.config.settings'), ('name', '=', field_name)])
    if not f:
        env['ir.model.fields'].create({
            'name': field_name,
            'model_id': env.ref('base.model_res_config_settings').id,
            'field_description': 'Allowed Users (POS)',
            'ttype': 'many2many',
            'relation': 'res.users',
            'related': 'pos_config_id.x_allowed_users',
            'readonly': False,
            'state': 'manual',
        })
    env.cr.commit()
    print("Field Created and Committed.")

    print("Step 2: Creating View")
    arch = '<xpath expr="//block[@id=\'pos_payment_section\']" position="before">'
    arch += '    <block title="Access Control Assignments" id="pos_access_section_v2">'
    arch += '        <setting string="Allowed Users" help="Limit visibility of this POS store.">'
    arch += '            <field name="' + field_name + '" widget="many2many_tags"/>'
    arch += '        </setting>'
    arch += '    </block>'
    arch += '</xpath>'
    
    v = env['ir.ui.view'].search([('name', '=', 'res.config.settings.pos.allowed.v3')])
    if not v:
        env['ir.ui.view'].create({
            'name': 'res.config.settings.pos.allowed.v3',
            'model': 'res.config.settings',
            'inherit_id': env.ref('point_of_sale.res_config_settings_view_form').id,
            'arch': arch
        })
    else:
        v.sudo().write({'arch': arch, 'active': True})
    
    env.cr.commit()
    print("View Created and Committed.")

except Exception as e:
    print(f"Error: {e}")
    env.cr.rollback()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/last_try.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/last_try.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    
    # Restart
    client.exec_command("systemctl restart odoo")
    client.close()
    print("Odoo restarted.")

if __name__ == "__main__":
    main()
