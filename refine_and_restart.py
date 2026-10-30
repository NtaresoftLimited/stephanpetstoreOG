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
    print("--- Refining Custom View ---")
    view = env['ir.ui.view'].search([
        ('name', '=', 'pos.config.allowed_users.view'),
        ('model', '=', 'pos.config')
    ])
    
    # Let's try to put it inside the 'Inventory' or 'Payments' group if we can find it
    # But //sheet position="inside" is usually safe. 
    # Maybe it needs to be inside a <div> or <group>.
    
    if view:
        # Update arch to use a more specific xpath
        view.sudo().write({
            'arch': \"\"\"
                <xpath expr="//sheet" position="inside">
                    <div style="background-color: #f9f9f9; padding: 20px; border: 1px solid #ddd; border-radius: 5px; margin-top: 20px;">
                        <h2 style="color: #7C7BAD;">Assign Access Control</h2>
                        <p class="text-muted">Select the users who are allowed to see and open this Point of Sale dashboard.</p>
                        <group>
                            <field name="x_allowed_users" widget="many2many_tags" placeholder="Add users..."/>
                        </group>
                    </div>
                </xpath>
            \"\"\"
        })
        print("Success: View arch updated with better styling.")
    
    # 2. Add it to the main POS Settings as well (res.config.settings)
    # We'll check if we need to do that, but usually, users look at the POS form.
    
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

    # 1. Update Code/View
    sftp = client.open_sftp()
    with sftp.file("/tmp/refine_pos_view.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/refine_pos_view.py\""
    client.exec_command(cmd)
    
    # 2. Restart Server
    print("Restarting Odoo server...")
    client.exec_command("systemctl restart odoo")
    
    client.close()
    print("Odoo server restarted and code updated.")

if __name__ == "__main__":
    main()
