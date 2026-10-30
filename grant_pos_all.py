
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
    print("GRANTING POS ACCESS TO ALL ACTIVE USERS")
    print("="*60)

    # Get all active users
    print("\n>> Active Users:")
    result = run_psql(client, "SELECT id, login FROM res_users WHERE active = true;")
    print(result)

    # Grant POS User (73) to all
    print("\n>> Granting POS User (73) to all active users...")
    for uid in [2, 4, 8, 9, 11]:
        sql = f"INSERT INTO res_groups_users_rel (gid, uid) VALUES (73, {uid}) ON CONFLICT DO NOTHING;"
        run_psql(client, sql)
        print(f"  Added user {uid} to group 73")

    # Grant POS Admin (74) to all
    print("\n>> Granting POS Admin (74) to all active users...")
    for uid in [2, 4, 8, 9, 11]:
        sql = f"INSERT INTO res_groups_users_rel (gid, uid) VALUES (74, {uid}) ON CONFLICT DO NOTHING;"
        run_psql(client, sql)
        print(f"  Added user {uid} to group 74")

    # Verify
    print("\n>> Verifying memberships...")
    result = run_psql(client, "SELECT u.login, r.gid FROM res_users u JOIN res_groups_users_rel r ON u.id = r.uid WHERE r.gid IN (73, 74) ORDER BY u.login, r.gid;")
    print(result)

    client.close()
    print("\nDone! Please log out and log back in to Odoo.")

if __name__ == "__main__":
    main()
