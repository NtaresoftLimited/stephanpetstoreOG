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
    pos_mikocheni = env['pos.config'].browse(7)
    if not pos_mikocheni.exists():
        pos_mikocheni = env['pos.config'].search([('name', 'ilike', 'Mikocheni')], limit=1)

    # 1. Close Open Sessions
    open_sessions = env['pos.session'].search([
        ('config_id', '=', pos_mikocheni.id),
        ('state', '!=', 'closed')
    ])
    
    if open_sessions:
        print(f"Force closing {len(open_sessions)} session(s)...")
        for s in open_sessions:
            print(f"Closing {s.name}...")
            if s.state in ['opening_control', 'opened']:
                s.action_pos_session_closing_control()
            s.sudo().action_pos_session_validate()
        env.cr.commit()
        print("Sessions closed.")

    # 2. Get/Create Mikocheni Cash PM (Using Journal 14)
    mikoc_cash_pm = env['pos.payment.method'].search([
        ('name', '=', 'Cash'),
        ('journal_id', '=', 14)
    ], limit=1)
    
    if not mikoc_cash_pm:
        print("Creating new Cash PM for Mikocheni...")
        mikoc_cash_pm = env['pos.payment.method'].create({
            'name': 'Cash',
            'journal_id': 14,
            'company_id': pos_mikocheni.company_id.id
        })
    else:
        print(f"Using existing Cash PM (ID: {mikoc_cash_pm.id})")

    # 3. Update Config
    target_pm_ids = [2, 4, 3, mikoc_cash_pm.id]
    print(f"Updating {pos_mikocheni.name} with PMs: {target_pm_ids}")
    pos_mikocheni.sudo().write({
        'payment_method_ids': [(6, 0, target_pm_ids)]
    })
    
    env.cr.commit()
    print("Success: Configuration updated.")
    
    # Final Verification
    print(f"Final Mikocheni Payment Methods: {[pm.name for pm in pos_mikocheni.payment_method_ids]}")

except Exception as e:
    print(f"Error: {e}")
    env.cr.rollback()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/final_close_and_update.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/final_close_and_update.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
