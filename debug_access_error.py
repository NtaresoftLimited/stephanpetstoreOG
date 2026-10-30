#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Investigating access error on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # 1. Check recent logs for access error
    print("\n>>> Recent Logs (searching for 'Access Error'):")
    cmd = "tail -n 100 /var/log/odoo/odoo.log | grep -C 5 -i 'Access Error' || tail -n 50 /var/log/odoo/odoo.log"
    stdin, stdout, stderr = client.exec_command(cmd)
    print(stdout.read().decode('utf-8', errors='replace'))

    queries = [
        # Check Websites
        ("Websites", "SELECT id, name, domain, company_id FROM website;"),
        
        # Check System Parameters (Base URL)
        ("Base URL", "SELECT key, value FROM ir_config_parameter WHERE key = 'web.base.url' OR key = 'web.base.url.freeze';"),
        
        # Check Default Website setting
        ("Public User Group", "SELECT id, name FROM res_groups WHERE name ILIKE '%Public%';"),
        
        # Check Public User
        ("Public User", "SELECT id, login, active, company_id, partner_id FROM res_users WHERE id = 4 OR login = 'public';"),
        
        # Check Companies
        ("Companies", "SELECT id, name FROM res_company;"),
    ]

    for name, query in queries:
        print(f"\n{'='*60}")
        print(f">>> {name}")
        print(f"{'='*60}")
        clean_query = ' '.join(query.split())
        cmd = f"su - postgres -c \"psql Stephans -c \\\"{clean_query}\\\"\""
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        if out:
            print(out)

    client.close()

if __name__ == "__main__":
    main()
