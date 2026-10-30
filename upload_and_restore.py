#!/usr/bin/env python3
"""
Upload and Fresh Restore
"""
import paramiko
import os
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
LOCAL_ZIP = r"D:\CODEX\STEPHANS OG\stephans-pet-app\Stephans_2026-01-27_12-19-23.zip"
REMOTE_ZIP = "/tmp/Stephans_2026-01-27_12-19-23.zip"

def main():
    print("="*60)
    print("UPLOADING BACKUP AND FRESH RESTORATION")
    print("="*60)
    
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    sftp = client.open_sftp()

    # 1. Upload backup file
    print(f"\n[1/16] Uploading backup file ({os.path.getsize(LOCAL_ZIP) // 1024 // 1024} MB)...")
    sftp.put(LOCAL_ZIP, REMOTE_ZIP, callback=lambda x, y: print(f"    Progress: {x*100//y}%", end="\r") if y > 0 else None)
    print("\n    Upload complete!")

    steps = [
        # 2. Stop Odoo
        ("Stopping Odoo", "systemctl stop odoo"),
        
        # 3. Kill any remaining processes
        ("Killing remaining processes", "pkill -9 -f odoo-bin 2>/dev/null || true"),
        
        # 4. Wait
        ("Waiting", "sleep 2"),
        
        # 5. Drop existing database
        ("Dropping Stephans database", "su - postgres -c 'dropdb --if-exists Stephans'"),
        
        # 6. Remove existing filestore
        ("Removing old filestore", "rm -rf /var/lib/odoo/.local/share/Odoo/filestore/Stephans"),
        
        # 7. Clear sessions
        ("Clearing sessions", "rm -rf /var/lib/odoo/.local/share/Odoo/sessions/*"),
        
        # 8. Extract backup fresh
        ("Extracting backup", f"rm -rf /tmp/restore_db && mkdir -p /tmp/restore_db && unzip -o {REMOTE_ZIP} -d /tmp/restore_db"),
        
        # 9. Create fresh database owned by odoo
        ("Creating fresh database", "su - postgres -c 'createdb -O odoo Stephans'"),
        
        # 10. Import SQL dump
        ("Importing SQL dump", "su - postgres -c 'psql -q Stephans < /tmp/restore_db/dump.sql'"),
        
        # 11. Create filestore directory
        ("Creating filestore directory", "mkdir -p /var/lib/odoo/.local/share/Odoo/filestore/Stephans"),
        
        # 12. Copy filestore
        ("Copying filestore", "cp -r /tmp/restore_db/filestore/* /var/lib/odoo/.local/share/Odoo/filestore/Stephans/"),
        
        # 13. Fix ALL permissions
        ("Fixing permissions", "chown -R odoo:odoo /var/lib/odoo"),
        
        # 14. Start Odoo
        ("Starting Odoo", "systemctl start odoo"),
        
        # 15. Wait for startup
        ("Waiting for startup", "sleep 5"),
        
        # 16. Verify
        ("Verifying", "systemctl is-active odoo && ss -tuln | grep 8069"),
    ]

    step_num = 2
    for name, cmd in steps:
        print(f"\n[{step_num}/16] {name}...")
        stdin, stdout, stderr = client.exec_command(cmd, timeout=600)
        exit_code = stdout.channel.recv_exit_status()
        out = stdout.read().decode('utf-8', errors='replace').strip()
        err = stderr.read().decode('utf-8', errors='replace').strip()
        
        if out and len(out) < 300:
            print(f"    {out}")
        elif out:
            print(f"    (output: {len(out)} chars - success)")
        
        if exit_code != 0:
            print(f"    Exit code: {exit_code}")
            if err and len(err) < 200:
                print(f"    {err}")
        
        step_num += 1

    sftp.close()
    client.close()
    
    print("\n" + "="*60)
    print("FRESH RESTORATION COMPLETE!")
    print("="*60)
    print("URL: http://166.1.227.63:8069/web/login")
    print("Database: Stephans")
    print("="*60)

if __name__ == "__main__":
    main()
