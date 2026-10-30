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
    print("--- Detailed POS - Journal Analysis ---")
    
    pos_configs = env['pos.config'].search([])
    for pos in pos_configs:
        print(f"\\nPOS: {pos.name}")
        for pm in pos.payment_method_ids:
            print(f"  PM: {pm.name} | Journal: {pm.journal_id.name if pm.journal_id else 'None'} | Journal ID: {pm.journal_id.id if pm.journal_id else 'None'}")

    # Check available cash journals that are NOT used in any PM
    all_cash_journals = env['account.journal'].search([('type', '=', 'cash')])
    used_cash_journals = env['pos.payment.method'].search([('journal_id.type', '=', 'cash')]).mapped('journal_id')
    
    unused_cash_journals = all_cash_journals - used_cash_journals
    print(f"\\nUnused Cash Journals: {[(j.id, j.name, j.code) for j in unused_cash_journals]}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/analyze_journals_deep.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/analyze_journals_deep.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
