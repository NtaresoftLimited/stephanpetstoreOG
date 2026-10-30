#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Fixing access issues on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    commands = [
        # 1. Activate Public User
        ("Activating Public User", "su - postgres -c \"psql Stephans -c \\\"UPDATE res_users SET active = true WHERE id = 4 OR login = 'public';\\\"\""),
        
        # 2. Update System Parameter (Base URL)
        ("Updating Base URL", "su - postgres -c \"psql Stephans -c \\\"UPDATE ir_config_parameter SET value = 'http://166.1.227.63:8069' WHERE key = 'web.base.url';\\\"\""),
        
        # 3. Ensure Admin has access to Company 1 (Stephan's Pet Store)
        ("Checking Admin Company Access", "su - postgres -c \"psql Stephans -c \\\"SELECT company_id FROM res_users WHERE id = 2;\\\"\""),
        
        # 4. Clear Caches
        ("Clearing Caches", "rm -rf /var/lib/odoo/.local/share/Odoo/sessions/*"),
        
        # 5. Restart Odoo
        ("Restarting Odoo", "systemctl restart odoo"),
    ]

    for name, cmd in commands:
        print(f"\n>>> {name}")
        stdin, stdout, stderr = client.exec_command(cmd)
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        if out:
            print(out)
        if err:
            print(f"STDERR: {err}")

    # Verify
    print("\n>>> Verification: Checking Public User Status")
    stdin, stdout, stderr = client.exec_command("su - postgres -c \"psql Stephans -c \\\"SELECT id, login, active FROM res_users WHERE id = 4;\\\"\"")
    print(stdout.read().decode('utf-8', errors='replace').strip())

    client.close()
    
    print("\n" + "="*60)
    print("FIX COMPLETE!")
    print("="*60)
    print("Please refresh your browser.")

if __name__ == "__main__":
    main()
