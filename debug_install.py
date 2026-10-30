#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Running debug install on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=120)

    # 1. Stop service
    print(">>> Stopping Odoo Service...")
    client.exec_command("systemctl stop odoo")

    # 2. Run install manually
    print(">>> Running install command...")
    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo.conf -d Stephans -i custom_pos_reports --stop-after-init > /tmp/install_out.log 2>&1\""
    client.exec_command(cmd)

    # 3. Read output
    print(">>> Reading log...")
    stdin, stdout, stderr = client.exec_command("cat /tmp/install_out.log")
    print(stdout.read().decode('utf-8', errors='replace'))

    # 4. Start service
    print(">>> Starting Odoo Service...")
    client.exec_command("systemctl start odoo")
    
    client.close()

if __name__ == "__main__":
    main()
