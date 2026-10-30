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

    open_sessions = env['pos.session'].search([
        ('config_id', '=', pos_mikocheni.id),
        ('state', '!=', 'closed')
    ])
    
    if not open_sessions:
        print("No open sessions found. Proceeding to update payment methods.")
    else:
        print(f"Closing {len(open_sessions)} session(s)...")
        for session in open_sessions:
            print(f"Closing session {session.name} (State: {session.state})...")
            # If in opening_control or opened, move to closing_control
            if session.state in ['opening_control', 'opened']:
                session.action_pos_session_closing_control()
            
            # Use sudo to validate and close
            # action_pos_session_validate usually finishes the job
            session.sudo().action_pos_session_validate()
            print(f"Session {session.name} closed.")

    # Now attempt Sync
    pos_masaki = env['pos.config'].browse(5)
    if not pos_masaki.exists():
        pos_masaki = env['pos.config'].search([('name', 'ilike', 'Masaki')], limit=1)

    print(f"Syncing payment methods from {pos_masaki.name} to {pos_mikocheni.name}...")
    masaki_pm_ids = pos_masaki.payment_method_ids.ids
    pos_mikocheni.sudo().write({
        'payment_method_ids': [(6, 0, masaki_pm_ids)]
    })
    
    env.cr.commit()
    print("Success: Payment methods synchronized.")
    
    # Final Verification
    new_m_pms = [pm.name for pm in pos_mikocheni.payment_method_ids]
    print(f"Final Mikocheni Payment Methods: {', '.join(new_m_pms)}")

except Exception as e:
    print(f"Error: {e}")
    env.cr.rollback()
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/close_and_sync_pm.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/close_and_sync_pm.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
