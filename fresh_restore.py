#!/usr/bin/env python3
"""
Fresh Database Restoration - Drop and Restore Clean
"""
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print("="*60)
    print("FRESH DATABASE RESTORATION")
    print("="*60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    steps = [
        # 1. Stop Odoo
        ("Stopping Odoo", "systemctl stop odoo"),
        
        # 2. Kill any remaining processes
        ("Killing remaining processes", "pkill -9 -f odoo-bin || true"),
        
        # 3. Wait
        ("Waiting", "sleep 2"),
        
        # 4. Drop existing database
        ("Dropping Stephans database", "su - postgres -c 'dropdb --if-exists Stephans'"),
        
        # 5. Remove existing filestore
        ("Removing old filestore", "rm -rf /var/lib/odoo/.local/share/Odoo/filestore/Stephans"),
        
        # 6. Clear sessions
        ("Clearing sessions", "rm -rf /var/lib/odoo/.local/share/Odoo/sessions/*"),
        
        # 7. Extract backup fresh
        ("Extracting backup", "rm -rf /tmp/restore_db && mkdir -p /tmp/restore_db && unzip -o /tmp/Stephans_2026-01-23_20-49-23.zip -d /tmp/restore_db"),
        
        # 8. Create fresh database owned by odoo
        ("Creating fresh database", "su - postgres -c 'createdb -O odoo Stephans'"),
        
        # 9. Import SQL dump
        ("Importing SQL dump (this takes a moment)", "su - postgres -c 'psql -q Stephans < /tmp/restore_db/dump.sql'"),
        
        # 10. Create filestore directory
        ("Creating filestore directory", "mkdir -p /var/lib/odoo/.local/share/Odoo/filestore/Stephans"),
        
        # 11. Copy filestore
        ("Copying filestore", "cp -r /tmp/restore_db/filestore/* /var/lib/odoo/.local/share/Odoo/filestore/Stephans/"),
        
        # 12. Fix ALL permissions
        ("Fixing permissions", "chown -R odoo:odoo /var/lib/odoo"),
        
        # 13. Start Odoo
        ("Starting Odoo", "systemctl start odoo"),
        
        # 14. Wait for startup
        ("Waiting for startup", "sleep 5"),
        
        # 15. Verify
        ("Verifying", "systemctl is-active odoo && ss -tuln | grep 8069"),
    ]

    for name, cmd in steps:
        print(f"\n[{steps.index((name, cmd)) + 1}/{len(steps)}] {name}...")
        stdin, stdout, stderr = client.exec_command(cmd, timeout=600)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        
        if out and len(out) < 500:
            print(f"    {out}")
        elif out:
            print(f"    (output: {len(out)} chars)")
        
        if exit_code != 0 and "dropdb" not in cmd:
            print(f"    WARNING: Exit code {exit_code}")
            if err:
                print(f"    STDERR: {err[:200]}")

    client.close()
    
    print("\n" + "="*60)
    print("FRESH RESTORATION COMPLETE!")
    print("="*60)
    print("URL: http://166.1.227.63:8069/web/login")
    print("Database: Stephans")
    print("="*60)

if __name__ == "__main__":
    main()
