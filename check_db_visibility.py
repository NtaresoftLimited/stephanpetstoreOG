#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking database visibility on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    checks = [
        # 1. List all PostgreSQL databases
        ("PostgreSQL Databases", "su - postgres -c 'psql -l'"),
        
        # 2. Check Stephans DB owner
        ("Stephans Owner", "su - postgres -c \"psql -c \\\"SELECT datname, pg_catalog.pg_get_userbyid(datdba) as owner FROM pg_database WHERE datname='Stephans';\\\"\""),
        
        # 3. Count tables in Stephans
        ("Tables in Stephans", "su - postgres -c \"psql Stephans -c \\\"SELECT count(*) FROM information_schema.tables WHERE table_schema='public';\\\"\""),
        
        # 4. Check res_users count
        ("Users in Stephans", "su - postgres -c \"psql Stephans -c 'SELECT count(*) FROM res_users;'\""),
        
        # 5. List actual usernames
        ("Login Users", "su - postgres -c \"psql Stephans -c \\\"SELECT id, login, active FROM res_users ORDER BY id LIMIT 10;\\\"\""),
        
        # 6. Check Odoo config for db_name or dbfilter
        ("Odoo DB Config", "grep -E 'db_name|dbfilter|list_db' /etc/odoo.conf || echo 'No db filter set'"),
        
        # 7. Check filestore exists
        ("Filestore", "ls -la /var/lib/odoo/.local/share/Odoo/filestore/ 2>/dev/null || echo 'No filestore found'"),
        
        # 8. Current Odoo logs
        ("Recent Logs", "tail -20 /var/log/odoo/odoo.log | grep -i -E 'error|stephans|database'"),
    ]

    for name, cmd in checks:
        print(f"\n{'='*60}")
        print(f">>> {name}")
        print(f"{'='*60}")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        if out:
            print(out)
        if err and "NOTICE" not in err:
            print(f"STDERR: {err}")

    client.close()

if __name__ == "__main__":
    main()
