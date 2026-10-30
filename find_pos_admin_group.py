#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
DB_NAME = "Stephans"

def run_psql(client, query):
    """Execute a PostgreSQL query and return the output."""
    cmd = f'su - postgres -c "psql {DB_NAME} -t -c \\"{query}\\""'
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode('utf-8', errors='replace').strip()

def main():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    print("\n" + "="*60)
    print("FINDING POS ADMIN GROUP")
    print("="*60)

    # Find groups in the same category as group 73 (POS User)
    print("\n>> Groups in POS Category (from Group 73):")
    groups = run_psql(client, """
        SELECT id, name
        FROM res_groups 
        WHERE category_id = (SELECT category_id FROM res_groups WHERE id = 73)
        ORDER BY id;
    """)
    print(groups)

    client.close()

if __name__ == "__main__":
    main()
