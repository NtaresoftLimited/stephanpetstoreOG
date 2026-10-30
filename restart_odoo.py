#!/usr/bin/env python3
import paramiko
import sys

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Connecting to {HOST} to restart Odoo...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)

    cmd = "systemctl restart odoo"
    
    stdin, stdout, stderr = client.exec_command(cmd)
    exit_status = stdout.channel.recv_exit_status()
    out = stdout.read().decode('utf-8', errors='replace').strip()
    err = stderr.read().decode('utf-8', errors='replace').strip()
    
    if exit_status == 0:
        print("Odoo service on the remote server has been successfully restarted.")
    else:
        print(f"Failed to restart. Error code: {exit_status}\\n{err}")

    client.close()

if __name__ == "__main__":
    main()
