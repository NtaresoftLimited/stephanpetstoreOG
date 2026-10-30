#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Debugging Odoo service on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # Check systemctl status
    print("\n>>> Systemctl status:")
    stdin, stdout, stderr = client.exec_command("systemctl status odoo --no-pager")
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # But ports are working, so maybe service just logged error but is running
    print("\n>>> Checking if Odoo processes are actually running:")
    stdin, stdout, stderr = client.exec_command("ps aux | grep -E 'odoo|python.*odoo' | grep -v grep")
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # Restart cleanly
    print("\n>>> Restarting Odoo service cleanly:")
    stdin, stdout, stderr = client.exec_command("systemctl restart odoo && sleep 3 && systemctl status odoo --no-pager")
    print(stdout.read().decode('utf-8', errors='replace'))

    client.close()

if __name__ == "__main__":
    main()
