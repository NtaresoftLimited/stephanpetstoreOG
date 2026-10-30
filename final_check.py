#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Final check on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    except Exception as e:
        print(f"SSH Failed: {e}")
        sys.exit(1)

    commands = [
        "ss -tuln | grep 8069",
        "ufw status",
        "tail -n 50 /var/log/odoo/odoo.log"
    ]

    for cmd in commands:
        print(f"\n>>> Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='replace').strip())

    client.close()

if __name__ == "__main__":
    main()
