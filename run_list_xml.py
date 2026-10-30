#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Listing ALL XMLs on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    
    sftp = client.open_sftp()
    sftp.put(r"D:\CODEX\STEPHANS OG\stephans-pet-app\list_all_xml.py", "/tmp/list_all_xml.py")
    
    cmd = "/usr/bin/python3 /tmp/list_all_xml.py"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    out = stdout.read().decode('utf-8', errors='replace')
    print(out[:5000]) # Cap output
    
    sftp.close()
    client.close()

if __name__ == "__main__":
    main()
