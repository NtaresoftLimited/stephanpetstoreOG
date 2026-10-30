#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking admin access rights on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    queries = [
        # Is admin a superuser?
        ("Admin Superuser Status", "SELECT id, login, active FROM res_users WHERE id = 2;"),
        
        # Check if admin is in Administrator group
        ("Admin in Administration Groups", """
            SELECT g.id, g.name::text 
            FROM res_groups g 
            JOIN res_groups_users_rel r ON r.gid = g.id 
            WHERE r.uid = 2 AND g.name::text ILIKE '%admin%' OR g.name::text ILIKE '%access%';
        """),
        
        # Check installed apps
        ("Installed POS Modules", """
            SELECT name, state 
            FROM ir_module_module 
            WHERE name LIKE 'point_of_sale%' OR name LIKE 'pos_%';
        """),
        
        # Menu visibility for admin
        ("POS Menu Items", """
            SELECT m.id, m.name::text, m.parent_id 
            FROM ir_ui_menu m 
            WHERE m.name::text ILIKE '%point%' OR m.name::text ILIKE '%pos%' 
            LIMIT 10;
        """),
        
        # Check recent Odoo logs for errors
    ]

    for name, query in queries:
        print(f"\n{'='*60}")
        print(f">>> {name}")
        print(f"{'='*60}")
        clean_query = ' '.join(query.split())
        cmd = f"su - postgres -c \"psql Stephans -c \\\"{clean_query}\\\"\""
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        if out:
            print(out)
        if err and "ERROR" in err:
            print(f"STDERR: {err}")

    # Check recent errors
    print(f"\n{'='*60}")
    print(">>> Recent Odoo Errors")
    print(f"{'='*60}")
    stdin, stdout, stderr = client.exec_command("tail -50 /var/log/odoo/odoo.log | grep -i error | tail -10")
    print(stdout.read().decode('utf-8', errors='replace').strip())

    client.close()

if __name__ == "__main__":
    main()
