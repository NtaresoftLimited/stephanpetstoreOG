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
    # IDs from previous inspection: Masaki (5), Mikocheni (7)
    pos_masaki = env['pos.config'].browse(5)
    pos_mikocheni = env['pos.config'].browse(7)
    
    if not pos_masaki.exists() or not pos_mikocheni.exists():
        # Search by name if IDs don't match for some reason
        pos_masaki = env['pos.config'].search([('name', 'ilike', 'Masaki')], limit=1)
        pos_mikocheni = env['pos.config'].search([('name', 'ilike', 'Mikocheni')], limit=1)

    print(f"--- Payment Methods Review ---")
    
    def print_pos_pm(pos):
        print(f"\\nPOS: {pos.name} (ID: {pos.id})")
        pm_names = [pm.name for pm in pos.payment_method_ids]
        print(f"Payment Methods: {', '.join(pm_names)}")
        return set(pos.payment_method_ids.ids)

    pm_ids_masaki = print_pos_pm(pos_masaki)
    pm_ids_mikocheni = print_pos_pm(pos_mikocheni)

    if pm_ids_masaki != pm_ids_mikocheni:
        print("\\nSTATUS: Payment methods are DIFFERENT.")
        missing = pm_ids_masaki - pm_ids_mikocheni
        extra = pm_ids_mikocheni - pm_ids_masaki
        if missing:
            m_names = [env['pos.payment.method'].browse(i).name for i in missing]
            print(f"Mikocheni is MISSING: {', '.join(m_names)}")
        if extra:
            e_names = [env['pos.payment.method'].browse(i).name for i in extra]
            print(f"Mikocheni has EXTRA: {', '.join(e_names)}")
    else:
        print("\\nSTATUS: Payment methods are identical.")

except Exception as e:
    print(f"Error: {e}")
"""

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    sftp = client.open_sftp()
    with sftp.file("/tmp/check_payment_methods.py", "w") as f:
        f.write(script)
    sftp.close()

    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell --no-http -c /etc/odoo.conf -d Stephans < /tmp/check_payment_methods.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    print(out)
    client.close()

if __name__ == "__main__":
    main()
