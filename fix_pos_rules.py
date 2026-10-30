
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def run_cmd(client, cmd):
    stdin, stdout, stderr = client.exec_command(cmd)
    return stdout.read().decode(), stderr.read().decode()

def run_psql(client, sql):
    cmd = f'su - odoo -c "psql -d Stephans -c \\"{sql}\\""'
    out, err = run_cmd(client, cmd)
    return out

def main():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    print("\n" + "="*60)
    print("CHECKING POS RECORD RULES")
    print("="*60)

    # Check for record rules on pos.session
    print("\n>> Record rules on pos.session model...")
    result = run_psql(client, "SELECT id, name, model_id, active, perm_read, perm_write FROM ir_rule WHERE model_id = (SELECT id FROM ir_model WHERE model = 'pos.session');")
    print(result)

    # Check model access rights
    print("\n>> Model access for pos.session...")
    result = run_psql(client, "SELECT a.id, a.name, g.name::text as group_name, a.perm_read, a.perm_write, a.perm_create, a.perm_unlink FROM ir_model_access a LEFT JOIN res_groups g ON a.group_id = g.id WHERE a.model_id = (SELECT id FROM ir_model WHERE model = 'pos.session');")
    print(result)

    # Restart Odoo
    print("\n>> Restarting Odoo service...")
    out, err = run_cmd(client, "systemctl restart odoo")
    print(f"stdout: {out}")
    print(f"stderr: {err}")

    import time
    time.sleep(5)

    # Check status
    out, err = run_cmd(client, "systemctl status odoo --no-pager")
    print(out)

    client.close()
    print("\nDone! Please try again after Odoo restarts.")

if __name__ == "__main__":
    main()
