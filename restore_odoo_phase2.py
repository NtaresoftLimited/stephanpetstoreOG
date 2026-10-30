#!/usr/bin/env python3
"""
SSH Helper Script for Odoo Database Restoration - Phase 2
Installs unzip and completes database restoration
"""
import paramiko
import sys

# Server credentials
HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def create_ssh_client():
    """Create and return an authenticated SSH client"""
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=30)
    return client

def run_command(client, cmd, timeout=300):
    """Execute a command and return output"""
    print(f"Running: {cmd}")
    stdin, stdout, stderr = client.exec_command(cmd, timeout=timeout)
    exit_code = stdout.channel.recv_exit_status()
    out = stdout.read().decode()
    err = stderr.read().decode()
    if out:
        print(f"  OUT: {out[:500]}{'...' if len(out) > 500 else ''}")
    if err:
        print(f"  ERR: {err[:500]}{'...' if len(err) > 500 else ''}")
    return exit_code, out, err

def main():
    print("=" * 60)
    print("Odoo Restoration - Phase 2")
    print("Installing unzip and completing restoration")
    print("=" * 60)
    
    # Connect
    print("\n[1/6] Connecting to server...")
    try:
        client = create_ssh_client()
        print("  Connected successfully!")
    except Exception as e:
        print(f"  FAILED: {e}")
        sys.exit(1)
    
    # Install unzip
    print("\n[2/6] Installing unzip...")
    run_command(client, "apt-get update -qq && apt-get install -y unzip", timeout=120)
    
    # Stop Odoo
    print("\n[3/6] Stopping Odoo...")
    run_command(client, "systemctl stop odoo || true")
    
    # Extract database backup
    print("\n[4/6] Extracting database backup...")
    run_command(client, "rm -rf /tmp/restore_db && mkdir -p /tmp/restore_db")
    code, out, err = run_command(client, "unzip -o /tmp/Stephans_2026-01-23_20-49-23.zip -d /tmp/restore_db")
    if code != 0:
        print("  FAILED to extract. Aborting.")
        sys.exit(1)
    
    # Restore database
    print("\n[5/6] Restoring PostgreSQL database...")
    run_command(client, 'su - postgres -c "dropdb Stephans" 2>/dev/null || true')
    run_command(client, 'su - postgres -c "createdb Stephans"')
    code, out, err = run_command(client, 'su - postgres -c "psql Stephans < /tmp/restore_db/dump.sql"', timeout=600)
    
    # Restore filestore
    print("\n[6/6] Restoring filestore and addons...")
    run_command(client, "mkdir -p /var/lib/odoo/.local/share/Odoo/filestore/Stephans")
    run_command(client, "cp -r /tmp/restore_db/filestore/* /var/lib/odoo/.local/share/Odoo/filestore/Stephans/ 2>/dev/null || true")
    run_command(client, "chown -R odoo:odoo /var/lib/odoo/.local/share/Odoo/filestore/Stephans")
    
    # Extract and deploy addons
    run_command(client, "rm -rf /tmp/addons_restore && mkdir -p /tmp/addons_restore")
    run_command(client, "unzip -o /tmp/addons.zip -d /tmp/addons_restore")
    run_command(client, "cp -r /tmp/addons_restore/* /usr/lib/python3/dist-packages/odoo/addons/ 2>/dev/null || true")
    
    # Start Odoo
    print("\nStarting Odoo...")
    run_command(client, "systemctl start odoo")
    
    client.close()
    
    print("\n" + "=" * 60)
    print("RESTORATION COMPLETE!")
    print("Access Odoo at: http://166.1.227.63:8069")
    print("=" * 60)

if __name__ == "__main__":
    main()
