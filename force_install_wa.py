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
        
        # 1. Stop Odoo
        print(">>> Stopping Odoo Service...")
        client.exec_command("systemctl stop odoo")
        time.sleep(2)

        # 2. Install whatsapp_connector ONLY
        print("\n>>> Installing whatsapp_connector...")
        cmd = "sudo -u odoo /usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo.conf -d Stephans -i whatsapp_connector --stop-after-init"
        print(f"Running: {cmd}")
        
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        
        print("--- Output ---")
        print(out[-1000:] if len(out) > 1000 else out)
        if err:
            print("--- Errors/Warnings ---")
            print(err[-1000:] if len(err) > 1000 else err)

        # 3. Start Odoo
        print("\n>>> Starting Odoo Service...")
        client.exec_command("systemctl start odoo")
        
        print("\n>>> Done.")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
