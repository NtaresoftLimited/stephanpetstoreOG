#!/usr/bin/env python3
import paramiko
import sys

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Fixing DB Ownership on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    except Exception as e:
        print(f"SSH Failed: {e}")
        sys.exit(1)

    commands = [
        # Change owner to odoo
        "su - postgres -c 'psql -c \"ALTER DATABASE \\\"Stephans\\\" OWNER TO odoo;\"'",
        
        # Verify
        "su - postgres -c 'psql -l | grep Stephans'",
        
        # Restart Odoo to refresh lists
        "systemctl restart odoo"
    ]

    for cmd in commands:
        print(f"\n>>> Running: {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode('utf-8', errors='replace').strip())
        err = stderr.read().decode('utf-8', errors='replace').strip()
        if err:
            print(f"STDERR: {err}")

    client.close()

if __name__ == "__main__":
    main()
