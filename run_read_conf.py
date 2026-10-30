#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Reading Config on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    
    sftp = client.open_sftp()
    sftp.put(r"D:\CODEX\STEPHANS OG\stephans-pet-app\read_conf.py", "/tmp/read_conf.py")
    
    cmd = "/usr/bin/python3 /tmp/read_conf.py"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    print(stdout.read().decode('utf-8', errors='replace'))
    print(stderr.read().decode('utf-8', errors='replace'))
    
    sftp.close()
    client.close()

if __name__ == "__main__":
    main()
