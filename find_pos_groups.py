
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def run_psql(client, sql):
    cmd = f'su - odoo -c "psql -d Stephans -c \\"{sql}\\""'
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode()

def main():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    print("\n" + "="*60)
    print("FINDING ALL POS-RELATED GROUPS")
    print("="*60)

    # Find all groups related to POS
    print("\n>> All groups containing 'pos' or 'sale'...")
    result = run_psql(client, "SELECT id, name::text FROM res_groups WHERE name::text ILIKE '%pos%' OR name::text ILIKE '%sale%' ORDER BY id;")
    print(result)

    # Find category for POS
    print("\n>> Finding POS module category...")
    result = run_psql(client, "SELECT id, name::text FROM ir_module_category WHERE name::text ILIKE '%point%' OR name::text ILIKE '%pos%';")
    print(result)

    # Find groups by category
    print("\n>> Groups in POS category...")
    result = run_psql(client, "SELECT g.id, g.name::text, c.name::text as category FROM res_groups g LEFT JOIN ir_module_category c ON g.category_id = c.id WHERE c.name::text ILIKE '%point%' OR c.name::text ILIKE '%pos%';")
    print(result)

    client.close()

if __name__ == "__main__":
    main()
