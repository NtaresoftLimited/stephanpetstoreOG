#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Fixing filestore permissions on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    commands = [
        # 1. Fix ownership of entire data_dir tree
        "chown -R odoo:odoo /var/lib/odoo",
        
        # 2. Verify filestore ownership
        "ls -la /var/lib/odoo/.local/share/Odoo/",
        
        # 3. Verify filestore subdir
        "ls -la /var/lib/odoo/.local/share/Odoo/filestore/",
        
        # 4. Clear Odoo asset cache (forces regeneration)
        "rm -rf /var/lib/odoo/.local/share/Odoo/sessions/*",
        
        # 5. Restart Odoo
        "systemctl restart odoo",
        
        # 6. Wait and verify
        "sleep 3 && systemctl is-active odoo",
    ]

    for cmd in commands:
        print(f"\n>>> {cmd}")
        stdin, stdout, stderr = client.exec_command(cmd)
        stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        if out:
            print(out)
        if err:
            print(f"STDERR: {err}")

    client.close()
    
    print("\n" + "="*60)
    print("PERMISSIONS FIXED!")
    print("="*60)
    print("Please refresh your browser (Ctrl+Shift+R) to see logos.")
    print("="*60)

if __name__ == "__main__":
    main()
