
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
    # Escape double quotes for shell, then for psql
    cmd = f'su - postgres -c "psql {DB_NAME} -c \\"{query}\\""'
    stdin, stdout, stderr = client.exec_command(cmd)
    data = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if err:
        print(f"STDERR: {err}")
    return data

def main():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    print("\n" + "="*60)
    print("CHECKING DATABASES")
    print("="*60)
    stdin, stdout, stderr = client.exec_command('su - postgres -c "psql -l"')
    print(stdout.read().decode())
    
    print("\n" + "="*60)
    print("CHECKING POS GROUPS AND USERS")
    print("="*60)

    # 1. Find POS Categories
    print("\n>> Finding POS Categories:")
    sql_cats = "SELECT id, name FROM ir_module_category WHERE name::text ILIKE '%Point of Sale%';"
    cats_out = run_psql(client, sql_cats)
    print(cats_out)

    # 2. Find Groups by Category
    print("\n>> Finding Groups in POS Categories:")
    # We'll valid IDs from previous output manually or just list all groups with a category that matches
    sql_groups = """
        SELECT g.id, g.name, c.name as category 
        FROM res_groups g 
        JOIN ir_module_category c ON g.category_id = c.id
        WHERE c.name::text ILIKE '%Point of Sale%';
    """
    groups_out = run_psql(client, sql_groups)
    print(groups_out)

    # 2. List Users and their Groups
    print("\n>> List Users (Limit 20):")
    sql_users = "SELECT id, login FROM res_users WHERE active = true ORDER BY id;"
    users_out = run_psql(client, sql_users)
    print(users_out)

    # 3. Check specific membership
    print("\n>> Check POS Membership for all users:")
    sql_membership = """
        SELECT u.login, g.name 
        FROM res_groups_users_rel rel
        JOIN res_users u ON rel.uid = u.id
        JOIN res_groups g ON rel.gid = g.id
        WHERE g.name::text ILIKE '%Point of Sale%'
        ORDER BY u.login;
    """
    mem_out = run_psql(client, sql_membership)
    print(mem_out)

    client.close()

if __name__ == "__main__":
    main()
