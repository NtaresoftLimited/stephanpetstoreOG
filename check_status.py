#!/usr/bin/env python3
import paramiko
import sys
import io

# Force UTF-8 for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking status of {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
        print("SSH Connection: SUCCESS")
    except Exception as e:
        print(f"SSH Connection: FAILED ({e})")
        sys.exit(1)

    commands = [
        "systemctl status odoo --no-pager",
        "netstat -tuln | grep 8069",
        "tail -n 50 /var/log/odoo/odoo-server.log",
        "grep 'addons_path' /etc/odoo/odoo.conf"
    ]

    for cmd in commands:
        print(f"\n>>> Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        print(out)
        if err:
            print(f"STDERR: {err}")

    client.close()

if __name__ == "__main__":
    main()
