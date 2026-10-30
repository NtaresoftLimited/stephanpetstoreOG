
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

    # Check model access rights for pos.session
    print("\n>> Model access for pos.session...")
    result = run_psql(client, "SELECT a.id, a.name, a.group_id, a.perm_read FROM ir_model_access a WHERE a.model_id = (SELECT id FROM ir_model WHERE model = 'pos.session');")
    print(result)

    # Check which user ID is currently active
    print("\n>> Your current login (assuming info@...)...")
    result = run_psql(client, "SELECT id, login FROM res_users WHERE login = 'info@stephanspetstore.co.tz';")
    print(result)

    # Check that user's groups
    print("\n>> Groups for user 2...")
    result = run_psql(client, "SELECT gid FROM res_groups_users_rel WHERE uid = 2;")
    print(result)

    # Check if group 73 is in that list
    print("\n>> Check if 73 (POS User) is assigned to user 2...")
    result = run_psql(client, "SELECT * FROM res_groups_users_rel WHERE uid = 2 AND gid = 73;")
    print(result)

    # Invalidate Odoo cache by updating the user
    print("\n>> Touch user record to invalidate cache...")
    result = run_psql(client, "UPDATE res_users SET write_date = NOW() WHERE id = 2;")
    print(result)

    client.close()
    print("\nDone! Clear browser cache and try again.")

if __name__ == "__main__":
    main()
