#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking POS config 7 and rules for User 12 on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    queries = [
        ("Store 7 Details", "SELECT id, name::text FROM pos_config WHERE id = 7;"),
        ("Check Rule 730 Groups", "SELECT g.id, g.name::text FROM res_groups g JOIN ir_rule_group_rel r ON r.gid = g.id WHERE r.rule_group_id = 730;"),
        ("Check Rule 731 Groups", "SELECT g.id, g.name::text FROM res_groups g JOIN ir_rule_group_rel r ON r.gid = g.id WHERE r.rule_group_id = 731;"),
        ("Check User 12 Groups", """
            SELECT g.id, g.name::text 
            FROM res_groups g 
            JOIN res_groups_users_rel r ON r.gid = g.id 
            WHERE r.uid = 12 AND (g.name::text ILIKE '%point%' OR g.name::text ILIKE '%pos%');
        """),
        ("Check pos.config field x_allowed_users", "SELECT column_name FROM information_schema.columns WHERE table_name = 'pos_config' AND column_name = 'x_allowed_users';"),
        ("Check Rule 275 Groups", "SELECT g.id, g.name::text FROM res_groups g JOIN ir_rule_group_rel r ON r.gid = g.id WHERE r.rule_group_id = 275;"),
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
