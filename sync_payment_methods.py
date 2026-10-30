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
    pos_masaki = env['pos.config'].browse(5)
    pos_mikocheni = env['pos.config'].browse(7)
    
    if not pos_masaki.exists() or not pos_mikocheni.exists():
        pos_masaki = env['pos.config'].search([('name', 'ilike', 'Masaki')], limit=1)
        pos_mikocheni = env['pos.config'].search([('name', 'ilike', 'Mikocheni')], limit=1)

    print(f"Syncing payment methods from {pos_masaki.name} to {pos_mikocheni.name}...")
    
    # Get IDs from Masaki
    masaki_pm_ids = pos_masaki.payment_method_ids.ids
    
    # Update Mikocheni
    pos_mikocheni.sudo().write({
        'payment_method_ids': [(6, 0, masaki_pm_ids)]
    })
    
    env.cr.commit()
    print("Success: Payment methods synchronized.")
    
    # Verification
    new_m_pms = [pm.name for pm in pos_mikocheni.payment_method_ids]
    print(f"New Mikocheni Payment Methods: {', '.join(new_m_pms)}")

except Exception as e:
    print(f"Error: {e}")
    env.cr.rollback()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/sync_payment_methods.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/sync_payment_methods.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
