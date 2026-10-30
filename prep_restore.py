#!/usr/bin/env python3
import paramiko
import os
import hashlib
import sys

# Configuration
HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
NEW_MASTER_PASS = "Ntare@2030!"
LOCAL_ZIP = r"D:\CODEX\STEPHANS OG\stephans-pet-app\Stephans_2026-01-23_20-49-23.zip"
REMOTE_ZIP = "/tmp/Stephans_2026-01-23_20-49-23.zip"

def get_local_checksum(path):
    """Calculate MD5 of local file (partial check for speed if large)"""
    # For 100MB, full hash is fine.
    print(f"Hashing local file: {path}...")
    hash_md5 = hashlib.md5()
    try:
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    except FileNotFoundError:
        print("Local file not found!")
        sys.exit(1)

def main():
    print(f"Configuration Update & Restore Prep for {HOST}...")
    
    # 1. Connect
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    except Exception as e:
        print(f"SSH Failed: {e}")
        sys.exit(1)

    # 2. Update Master Password
    print("\n>>> Updating Master Password in /etc/odoo.conf...")
    # Escape special chars if needed, but '!' usually ok in sed if quoted with single quotes, 
    # but python subprocess might complicate. 
    # Use proper sed syntax. 'Ntare@2030!' -> need to be careful with ! in bash history but here it is exec_command.
    sed_cmd = f"sed -i 's/^admin_passwd = .*/admin_passwd = {NEW_MASTER_PASS}/' /etc/odoo.conf"
    stdin, stdout, stderr = client.exec_command(sed_cmd)
    exit_status = stdout.channel.recv_exit_status()
    if exit_status == 0:
        print("Success: Config updated.")
    else:
        print(f"Error updating config: {stderr.read().decode()}")

    # 3. Verify Remote File
    print("\n>>> Verifying Remote Backup File...")
    # Check if exists and get md5
    check_cmd = f"md5sum {REMOTE_ZIP}"
    stdin, stdout, stderr = client.exec_command(check_cmd)
    remote_out = stdout.read().decode().strip()
    
    if not remote_out or "No such file" in remote_out:
        print("Remote file missing. Needs upload.")
        sys.exit(2) # Exit code 2 triggers upload flow
    
    remote_md5 = remote_out.split()[0]
    local_md5 = get_local_checksum(LOCAL_ZIP)
    
    print(f"Local MD5:  {local_md5}")
    print(f"Remote MD5: {remote_md5}")
    
    if local_md5 == remote_md5:
        print("Files MATCH. Proceeding with restore script.")
    else:
        print("Files MISMATCH. Needs re-upload.")
        sys.exit(2)

    client.close()

if __name__ == "__main__":
    main()
