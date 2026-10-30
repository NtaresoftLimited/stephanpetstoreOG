#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking admin user and company setup on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    queries = [
        # Admin user details
        ("Admin User Info", """
            SELECT u.id, u.login, u.active, p.name, u.company_id 
            FROM res_users u 
            JOIN res_partner p ON u.partner_id = p.id 
            WHERE u.login = 'admin';
        """),
        
        # All companies
        ("Companies", "SELECT id, name FROM res_company;"),
        
        # Admin's companies (multi-company)
        ("Admin's Allowed Companies", """
            SELECT c.id, c.name 
            FROM res_company c 
            JOIN res_company_users_rel r ON r.cid = c.id 
            WHERE r.user_id = 2;
        """),
        
        # Admin's groups (access rights)
        ("Admin Groups (Sample)", """
            SELECT g.name 
            FROM res_groups g 
            JOIN res_groups_users_rel r ON r.gid = g.id 
            WHERE r.uid = 2 
            LIMIT 10;
        """),
        
        # Check POS data company
        ("POS Orders by Company", """
            SELECT company_id, count(*) 
            FROM pos_order 
            GROUP BY company_id;
        """),
        
        # Check if admin has POS access
        ("Admin POS Access", """
            SELECT g.name 
            FROM res_groups g 
            JOIN res_groups_users_rel r ON r.gid = g.id 
            WHERE r.uid = 2 AND g.name ILIKE '%point%' OR g.name ILIKE '%pos%';
        """),
        
        # Sample partners/customers
        ("Sample Partners", "SELECT id, name, company_id FROM res_partner WHERE customer_rank > 0 LIMIT 5;"),
        
        # Products by company
        ("Products by Company", """
            SELECT company_id, count(*) 
            FROM product_template 
            GROUP BY company_id;
        """),
    ]

    for name, query in queries:
        print(f"\n{'='*60}")
        print(f">>> {name}")
        print(f"{'='*60}")
        # Clean up the query for command line
        clean_query = ' '.join(query.split())
        cmd = f"su - postgres -c \"psql Stephans -c \\\"{clean_query}\\\"\""
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        if out:
            print(out)
        if err and "NOTICE" not in err and "rows)" not in err:
            print(f"STDERR: {err}")

    client.close()

if __name__ == "__main__":
    main()
