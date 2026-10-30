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

    print(f"Preparing payment methods for {pos_mikocheni.name}...")

    # 1. Ensure "Customer Account" (ID 3) is added
    # 2. Add existing Card (2) and Selcom (4)
    # 3. Create a NEW "Cash" payment method for Mikocheni using Journal 14
    
    # Check if a Cash method specifically for Mikocheni already exists but isn't linked
    existing_mikoc_cash = env['pos.payment.method'].search([
        ('name', '=', 'Cash'),
        ('journal_id', '=', 14)
    ], limit=1)
    
    if existing_mikoc_cash:
        print(f"Found existing Cash PM for Mikocheni (ID: {existing_mikoc_cash.id})")
        mikoc_cash_pm = existing_mikoc_cash
    else:
        print("Creating new Cash PM for Mikocheni using Journal 14...")
        mikoc_cash_pm = env['pos.payment.method'].create({
            'name': 'Cash',
            'journal_id': 14,
            'company_id': pos_mikocheni.company_id.id
        })
        print(f"Created Cash PM (ID: {mikoc_cash_pm.id})")

    # Current target PM set: Card(2), Selcom(4), Customer Account(3), and Mikoc Cash
    target_pm_ids = [2, 4, 3, mikoc_cash_pm.id]
    
    pos_mikocheni.sudo().write({
        'payment_method_ids': [(6, 0, target_pm_ids)]
    })
    
    env.cr.commit()
    print("Success: Payment methods updated for Mikocheni.")
    
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
    with sftp.file("/tmp/fix_mikocheni_pms_final.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/fix_mikocheni_pms_final.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
