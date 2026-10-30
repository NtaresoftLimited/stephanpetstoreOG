#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Fixing stuck modules and checking users on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # Check info@ user
    print("\n>>> Checking info@stephanspetstore.co.tz user:")
    cmd = "su - postgres -c \"psql Stephans -c \\\"SELECT id, login, active, company_id FROM res_users WHERE login = 'info@stephanspetstore.co.tz';\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace').strip())
    
    # Fix stuck module - set to 'installed' or 'uninstalled'
    print("\n>>> Fixing stuck pos_excel_reports_app_v18 module:")
    cmd = "su - postgres -c \"psql Stephans -c \\\"UPDATE ir_module_module SET state = 'uninstalled' WHERE name = 'pos_excel_reports_app_v18' AND state = 'to upgrade';\\\"\""
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace').strip())

    # Clear caches and restart
    print("\n>>> Clearing caches and restarting Odoo:")
    commands = [
        "systemctl stop odoo",
        "rm -rf /var/lib/odoo/.local/share/Odoo/sessions/*",
        "su - postgres -c \"psql Stephans -c 'DELETE FROM ir_attachment WHERE name LIKE \\\"web.assets%\\\" OR name LIKE \\\"point_of_sale.assets%\\\";'\"",
        "systemctl start odoo",
        "sleep 5",
        "systemctl is-active odoo"
    ]
    
    for cmd in commands:
        print(f"   {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', errors='replace').strip()
        if out:
            print(f"   -> {out}")

    client.close()
    
    print("\n" + "="*60)
    print("FIXES APPLIED!")
    print("="*60)
    print("Please try logging in again with:")
    print("  Email: info@stephanspetstore.co.tz")
    print("  Password: Stephan@3202")
    print("="*60)

if __name__ == "__main__":
    main()
