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
    cmd = f'su - postgres -c "psql {DB_NAME} -c \\"{query}\\""'
    stdin, stdout, stderr = client.exec_command(cmd)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err and "NOTICE" not in err: print(f"STDERR: {err}")

def main():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    print("\n" + "="*60)
    print("GRANTING POS ADMINISTRATOR ACCESS (Users: 2, 11)")
    print("="*60)

    users_to_add = [2, 11]
    
    for uid in users_to_add:
        print(f"\n>> Processing User {uid}...")
        
        # 1. Remove from 'User' group (73) just in case
        print(f"   Removing from POS 'User' group (73)...")
        run_psql(client, f"DELETE FROM res_groups_users_rel WHERE gid = 73 AND uid = {uid};")
        
        # 2. Add to 'Administrator' group (74)
        print(f"   Adding to POS 'Administrator' group (74)...")
        # Try insert, ignore if exists
        sql_insert = f"INSERT INTO res_groups_users_rel (gid, uid) VALUES (74, {uid}) ON CONFLICT DO NOTHING;"
        # In case ON CONFLICT is not supported or constraint name is different, we can just try and ignore error
        # But usually res_groups_users_rel has a unique index.
        # Let's try simple insert and catch error in psql output if any, essentially 'doing nothing' on duplicate
        run_psql(client, sql_insert)

    # 3. Verify
    print("\n>> Verifying changes...")
    verify_query = """
        SELECT u.login, g.name->>'en_US'
        FROM res_groups g 
        JOIN res_groups_users_rel rel ON g.id = rel.gid 
        JOIN res_users u ON rel.uid = u.id
        WHERE (rel.uid = 2 OR rel.uid = 11) AND (g.id = 73 OR g.id = 74);
    """
    run_psql(client, verify_query)

    client.close()
    print("\nDone! User 11 should now have full POS reporting access.")

if __name__ == "__main__":
    main()
