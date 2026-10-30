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
    print("--- Investigating Journals and Payment Methods ---")
    
    # 1. List all Cash/Bank journals
    journals = env['account.journal'].search([('type', 'in', ['cash', 'bank'])])
    print("\\nJournals:")
    for j in journals:
        print(f"ID: {j.id} | Name: {j.name} | Type: {j.type} | Code: {j.code}")
    
    # 2. List all POS Payment Methods
    pms = env['pos.payment.method'].search([])
    print("\\nPOS Payment Methods:")
    for pm in pms:
        print(f"ID: {pm.id} | Name: {pm.name} | Journal: {pm.journal_id.name if pm.journal_id else 'None'}")

    # 3. Check Masaki's specific set
    pos_masaki = env['pos.config'].browse(5)
    print(f"\\nMasaki PMs: {[(pm.id, pm.name) for pm in pos_masaki.payment_method_ids]}")
    
    # 4. Check Mikocheni's current set
    pos_mikocheni = env['pos.config'].browse(7)
    print(f"Mikocheni PMs: {[(pm.id, pm.name) for pm in pos_mikocheni.payment_method_ids]}")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/investigate_pms.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/investigate_pms.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
