#!/usr/bin/env python3
"""
SSH Helper Script for Odoo Database Restoration
Uses paramiko for non-interactive SSH authentication
"""
import paramiko
import os
import sys

# Server credentials
HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

# Files to transfer
LOCAL_DB_BACKUP = r"D:\CODEX\STEPHANS OG\stephans-pet-app\Stephans_2026-01-23_20-49-23.zip"
LOCAL_ADDONS = r"D:\CODEX\STEPHANS OG\stephans-pet-app\addons.zip"   
REMOTE_TMP = "/tmp/"

def create_ssh_client():
    """Create and return an authenticated SSH client"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    return client

def transfer_file(sftp, local_path, remote_path):
    """Transfer a file via SFTP"""
    filename = os.path.basename(local_path)
    remote_file = os.path.join(remote_path, filename).replace("\\", "/")
    print(f"Transferring {filename} to {remote_file}...")
    sftp.put(local_path, remote_file, callback=lambda x, y: print(f"  Progress: {x}/{y} bytes", end="\r"))
    print(f"\n  Done: {filename}")
    return remote_file

def run_command(client, cmd):
    """Execute a command and return output"""
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(f"  OUT: {out}")
    if err:
        print(f"  ERR: {err}")
    return exit_code, out, err

def main():
    print("=" * 60)
    print("Odoo Database Restoration Script")
    print("=" * 60)
    
    # Step 1: Connect
    print("\n[1/5] Connecting to server...")
    try:
        client = create_ssh_client()
        sftp = client.open_sftp()
        print("  Connected successfully!")
    except Exception as e:
        print(f"  FAILED: {e}")
        sys.exit(1)
    
    # Step 2: Transfer files
    # print("\n[2/5] Transferring backup files...")
    # try:
    #     remote_db = transfer_file(sftp, LOCAL_DB_BACKUP, REMOTE_TMP)
    #     remote_addons = transfer_file(sftp, LOCAL_ADDONS, REMOTE_TMP)
    # except Exception as e:
    #     print(f"  Transfer FAILED: {e}")
    #     sys.exit(1)
    remote_db = "/tmp/Stephans_2026-01-23_20-49-23.zip"
    remote_addons = "/tmp/addons.zip"
    
    # Step 3: Stop Odoo
    print("\n[3/5] Stopping Odoo service...")
    run_command(client, "systemctl stop odoo || true")
    
    # Step 4: Extract and Restore Database
    print("\n[4/5] Restoring database...")
    commands = [
        f"mkdir -p /tmp/restore_db && unzip -o {remote_db} -d /tmp/restore_db",
        "su - postgres -c \"dropdb Stephans 2>/dev/null || true\"",
        "su - postgres -c \"createdb Stephans\"",
        "su - postgres -c \"psql Stephans < /tmp/restore_db/dump.sql\"",
        "mkdir -p /var/lib/odoo/.local/share/Odoo/filestore/Stephans",
        "cp -r /tmp/restore_db/filestore/* /var/lib/odoo/.local/share/Odoo/filestore/Stephans/ 2>/dev/null || true",
        "chown -R odoo:odoo /var/lib/odoo/.local/share/Odoo/filestore/Stephans",
    ]
    for cmd in commands:
        code, out, err = run_command(client, cmd)
        if code != 0 and "already exists" not in err and "does not exist" not in err:
            print(f"  Warning: Command may have failed (exit code {code})")
    
    # Step 5: Deploy addons and restart
    print("\n[5/5] Deploying addons and restarting Odoo...")
    addon_commands = [
        f"mkdir -p /tmp/addons_restore && unzip -o {remote_addons} -d /tmp/addons_restore",
        "cp -r /tmp/addons_restore/* /opt/odoo/custom-addons/ 2>/dev/null || true",
        "chown -R odoo:odoo /opt/odoo/custom-addons",
        "systemctl restart odoo",
    ]
    for cmd in addon_commands:
        run_command(client, cmd)
    
    # Cleanup
    sftp.close()
    client.close()
    
    print("\n" + "=" * 60)
    print("RESTORATION COMPLETE!")
    print("Access Odoo at: http://166.1.227.63:8069")
    print("=" * 60)

if __name__ == "__main__":
    main()
