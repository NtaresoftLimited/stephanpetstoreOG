#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
MODULE_NAME = "custom_pos_reports"

def main():
    print(f"Forcing installation of {MODULE_NAME} on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)

    commands = [
        # 1. Stop Odoo service
        ("Stopping Odoo", "systemctl stop odoo"),
        
        # 2. Run update command manually
        ("Forcing Module Update", f"su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin -c /etc/odoo.conf -d Stephans -u {MODULE_NAME} --stop-after-init\""),
        
        # 3. Start Odoo service
        ("Starting Odoo", "systemctl start odoo"),
        
        # 4. Verify installation
        ("Verifying Installation", f"su - postgres -c \"psql Stephans -c \\\"SELECT name, state FROM ir_module_module WHERE name='{MODULE_NAME}';\\\"\"")
    ]

    for name, cmd in commands:
        print(f"\n>>> {name}")
        # Increase timeout for the update command as it might take time
        timeout = 300 if "Forcing" in name else 30
        stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        
        if out: print(out)
        if exit_code != 0:
            print(f"Exit Code: {exit_code}")
            if err: print(f"STDERR: {err}")
        elif err and "Forcing" in name:
             # Odoo logs to stderr usually
             print(f"Logs: {err[-500:]}")

    client.close()
    
    print("\n" + "="*60)
    print("INSTALLATION COMPLETE!")
    print("="*60)

if __name__ == "__main__":
    main()
