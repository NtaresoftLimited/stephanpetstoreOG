#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking logs on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    cmd = "tail -n 600 /var/log/odoo/odoo.log"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    with open("server_log.txt", "w", encoding='utf-8') as f:
        f.write(stdout.read().decode('utf-8', errors='replace'))
        
    print("Logs saved to server_log.txt")
    client.close()

if __name__ == "__main__":
    main()
