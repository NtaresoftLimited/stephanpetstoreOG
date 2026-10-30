import paramiko
import sys

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def run_command(client, command):
    print(f"\n>>> Running: {command}")
    stdin, stdout, stderr = client.exec_command(command)
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    if out: print(out)
    if err: print(f"STDERR: {err}")
    return out, err

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    # 1. Check data directory
    run_command(client, "grep 'data_dir' /etc/odoo.conf")
    
    # 2. Check current databases
    run_command(client, "su - postgres -c 'psql -l'")

    # 3. Create temp restore dir
    run_command(client, "rm -rf /tmp/restore_data && mkdir /tmp/restore_data")
    
    # 4. Unzip backup
    run_command(client, "unzip /tmp/restore_backup.zip -d /tmp/restore_data")

    # 5. Stop Odoo
    run_command(client, "systemctl stop odoo")

    # 6. Drop and Recreate database Stephans
    # Terminate connections first
    run_command(client, "su - postgres -c \"psql -c \\\"SELECT pg_terminate_backend(pg_stat_activity.pid) FROM pg_stat_activity WHERE pg_stat_activity.datname = 'Stephans' AND pid <> pg_backend_pid();\\\"\"")
    run_command(client, "su - postgres -c 'dropdb Stephans'")
    run_command(client, "su - postgres -c 'createdb Stephans'")

    # 7. Restore SQL dump
    run_command(client, "su - postgres -c 'psql Stephans < /tmp/restore_data/dump.sql'")

    # 8. Restore filestore
    # We need to find where the filestore goes. Usually /var/lib/odoo/.local/share/Odoo/filestore/Stephans
    # Let's try to find the actual data_dir
    out, err = run_command(client, "grep 'data_dir' /etc/odoo.conf")
    data_dir = "/var/lib/odoo" # default
    if out and "=" in out:
        data_dir = out.split("=")[1].strip()
    
    filestore_path = f"{data_dir}/.local/share/Odoo/filestore/Stephans"
    print(f"Target filestore path: {filestore_path}")
    
    run_command(client, f"mkdir -p {filestore_path}")
    run_command(client, f"cp -r /tmp/restore_data/filestore/* {filestore_path}/")
    run_command(client, f"chown -R odoo:odoo {data_dir}")

    # 9. Start Odoo
    run_command(client, "systemctl start odoo")
    
    # 10. Check logs
    run_command(client, "tail -n 50 /var/log/odoo/odoo-server.log")

    client.close()

if __name__ == "__main__":
    main()
