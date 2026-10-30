#!/usr/bin/env python3
import paramiko
import sys

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Fixing addons on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    except Exception as e:
        print(f"SSH Failed: {e}")
        sys.exit(1)

    commands = [
        # 1. Create custom-addons dir if missing
        "mkdir -p /opt/odoo/custom-addons",
        
        # 2. Check if I put files in the wrong place and move them
        "if [ -d /usr/lib/python3/dist-packages/odoo/addons/pos_dynamic_discount ]; then cp -r /usr/lib/python3/dist-packages/odoo/addons/* /opt/odoo/custom-addons/; fi",
        "if [ -d /usr/lib/python3/dist-packages/odoo/addons/grooming ]; then cp -r /usr/lib/python3/dist-packages/odoo/addons/grooming /opt/odoo/custom-addons/; fi",

        # 3. Ensure permissions are correct
        "chown -R odoo:odoo /opt/odoo/custom-addons",
        "chmod -R 755 /opt/odoo/custom-addons",

        # 4. Restart Odoo
        "systemctl restart odoo",
        "sleep 5",
        "systemctl status odoo --no-pager"
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
