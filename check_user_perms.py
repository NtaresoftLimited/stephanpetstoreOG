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
    print("CHECKING USER PERMISSIONS (User ID: 11)")
    print("="*60)

    # 1. Identify User
    print("\n>> User Details:")
    user_info = run_psql(client, "SELECT id, name, login, active FROM res_users WHERE id = 11;")
    print(user_info)

    # 2. Check Current Groups for User 11
    print("\n>> Current Groups for User 11:")
    groups = run_psql(client, """
        SELECT g.id, g.name, c.name as category
        FROM res_groups g 
        JOIN res_groups_users_rel rel ON g.id = rel.gid 
        LEFT JOIN ir_module_category c ON g.category_id = c.id
        WHERE rel.uid = 11 
        ORDER BY c.name, g.name;
    """)
    print(groups)

    # 3. List Available POS Groups
    print("\n>> Available POS Security Groups:")
    pos_groups = run_psql(client, """
        SELECT g.id, g.name, c.name as category
        FROM res_groups g
        LEFT JOIN ir_module_category c ON g.category_id = c.id
        WHERE c.name ILIKE '%Point of Sale%' OR g.name ILIKE '%Point of Sale%'
        ORDER BY g.id;
    """)
    print(pos_groups)

    client.close()

if __name__ == "__main__":
    main()
