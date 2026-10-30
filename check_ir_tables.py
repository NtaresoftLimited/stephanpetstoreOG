#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking rule/group relations and user groups on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    queries = [
        ("List all IR tables", "SELECT tablename FROM pg_tables WHERE tablename LIKE 'ir_%rule%';"),
        ("Check rule_group_rel columns", "SELECT column_name FROM information_schema.columns WHERE table_name = 'rule_group_rel';"),
        ("Check User 12 All Groups", "SELECT g.name::text FROM res_groups g JOIN res_groups_users_rel r ON r.gid = g.id WHERE r.uid = 12;"),
        ("Check POS Config 7 fields", "SELECT column_name FROM information_schema.columns WHERE table_name = 'pos_config' AND (column_name ILIKE '%employee%' OR column_name ILIKE '%user%');"),
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

    client.close()

if __name__ == "__main__":
    main()
