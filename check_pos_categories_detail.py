#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking POS category details on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    queries = [
        ("Categories with Parent", "SELECT id, name::text, parent_id FROM ir_module_category WHERE id IN (49, 59, 88, 134);"),
        ("Groups for Category 134", "SELECT id, name::text FROM res_groups WHERE category_id = 134;"),
        ("Groups for Category 59", "SELECT id, name::text FROM res_groups WHERE category_id = 59;"),
        ("Groups for Category 49", "SELECT id, name::text FROM res_groups WHERE category_id = 49;"),
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
