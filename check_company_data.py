#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking and fixing company access on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # First, let's see more details
    queries = [
        # Which company has POS configs?
        ("POS Configs by Company", "SELECT id, name, company_id FROM pos_config;"),
        
        # Which company has the most data?
        ("Sale Orders by Company", "SELECT company_id, count(*) FROM sale_order GROUP BY company_id;"),
        
        # Check invoices
        ("Invoices by Company", "SELECT company_id, count(*) FROM account_move GROUP BY company_id;"),
        
        # Check which users belong to which company
        ("Users by Company", """
            SELECT u.login, u.company_id, c.name as company_name 
            FROM res_users u 
            JOIN res_company c ON u.company_id = c.id 
            WHERE u.active = true;
        """),
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
