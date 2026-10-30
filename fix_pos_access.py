
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
    print("FIXING POS ACCESS FOR ALL ADMINS")
    print("="*60)

    # 1. Find POS groups
    print("\n>> Finding POS Groups...")
    result = run_psql(client, "SELECT id, name::text FROM res_groups WHERE name::text ILIKE '%point of sale%';")
    print(result)

    # 2. Find all admin users (group 1 is usually 'Administration / Settings')
    print("\n>> Finding Admin Users...")
    result = run_psql(client, "SELECT u.id, u.login FROM res_users u JOIN res_groups_users_rel r ON u.id = r.uid WHERE r.gid = 1;")
    print(result)
    
    # 3. Grant POS User (73) and POS Admin (74) to ALL users
    print("\n>> Granting POS Access to ALL users...")
    
    # Get all user IDs
    result = run_psql(client, "SELECT id FROM res_users WHERE active = true;")
    print(f"Active users: {result}")
    
    # Grant POS User group (73) to all active users
    sql = "INSERT INTO res_groups_users_rel (gid, uid) SELECT 73, id FROM res_users WHERE active = true ON CONFLICT DO NOTHING;"
    run_psql(client, sql)
    print("Granted POS User to all active users.")
    
    # Grant POS Admin group (74) to admin users (those with Settings group = 1)
    sql = "INSERT INTO res_groups_users_rel (gid, uid) SELECT 74, uid FROM res_groups_users_rel WHERE gid = 1 ON CONFLICT DO NOTHING;"
    run_psql(client, sql)
    print("Granted POS Admin to all Settings admins.")
    
    # 4. Verify
    print("\n>> Verifying POS Group Memberships...")
    result = run_psql(client, "SELECT u.login, g.name::text FROM res_users u JOIN res_groups_users_rel r ON u.id = r.uid JOIN res_groups g ON r.gid = g.id WHERE g.name::text ILIKE '%point of sale%' ORDER BY u.login;")
    print(result)

    client.close()
    print("\nDone! Please refresh Odoo.")

if __name__ == "__main__":
    main()
