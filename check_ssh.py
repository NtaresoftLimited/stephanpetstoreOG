#!/usr/bin/env python3
import paramiko
import sys
import io

# Force UTF-8 for stdout
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking SSH status of {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
        print("SSH Connection: SUCCESS")
        
        # Check uptime to see if it rebooted
        stdin, stdout, stderr = client.exec_command("uptime")
        print(f"Uptime: {stdout.read().decode().strip()}")
        
        client.close()
    except Exception as e:
        print(f"SSH Connection: FAILED ({e})")
        sys.exit(1)

if __name__ == "__main__":
    main()
