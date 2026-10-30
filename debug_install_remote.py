import paramiko
import sys
import time

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
        
        # 1. Fix permissions just in case
        print("\n>>> Fixing permissions (chown -R odoo:odoo)...")
        client.exec_command("chown -R odoo:odoo /opt/odoo/custom-addons/whatsapp_connector")
        
        # 2. Check Odoo Log
        print("\n>>> Checking Odoo Log (/var/log/odoo/odoo.log) last 100 lines:")
        stdin, stdout, stderr = client.exec_command("tail -n 100 /var/log/odoo/odoo.log")
        log_content = stdout.read().decode('utf-8', errors='replace')
        print(log_content)
        
        # 3. Check module status via shell command (using python to query DB)
        print("\n>>> Checking module status in DB via Odoo Shell:")
        # We construct a python script to run inside Odoo shell
        # or use psql if available. Using psql is faster and easier.
        
        psql_cmd = "su - postgres -c 'psql -d Stephans -c \"select name, state from ir_module_module where name = ''whatsapp_connector'';\"'"
        stdin, stdout, stderr = client.exec_command(psql_cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())
        
        # 4. If not installed, try to force install again and capture output
        # We will try to run the install command and print output
        # But we won't stop the running service this time, we'll just see if we can trigger update?
        # No, can't run two instances on same port/db usually unless one is a worker.
        # But we can run with --stop-after-init to update.
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
