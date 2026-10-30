#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Unzipping Backup on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=60)
    
    # Clean previous
    client.exec_command("rm -rf /tmp/restore_data")
    client.exec_command("mkdir -p /tmp/restore_data")
    
    # Unzip
    print(">>> Unzipping...")
    cmd = "unzip -q /tmp/restore_source.zip -d /tmp/restore_data"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    err = stderr.read().decode()
    if err:
        print(f"Stats: {err}")
    else:
        print("Unzip successful.")
        
    # List contents
    stdin, stdout, stderr = client.exec_command("ls -F /tmp/restore_data")
    print(stdout.read().decode())

    client.close()

if __name__ == "__main__":
    main()
