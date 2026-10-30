#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking restore process on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # Check for upload/unzip/psql processes
    stdin, stdout, stderr = client.exec_command("ps aux | grep -E 'python|psql|unzip' | grep -v grep")
    print(stdout.read().decode('utf-8', errors='replace'))
    
    # Check disk usage to see if restore is filling up
    stdin, stdout, stderr = client.exec_command("df -h /")
    print("\nDisk Usage:")
    print(stdout.read().decode('utf-8', errors='replace'))

    client.close()

if __name__ == "__main__":
    main()
