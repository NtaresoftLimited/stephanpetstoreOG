#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Running Real Restore on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=600) # Long timeout for 500+ images
    
    sftp = client.open_sftp()
    sftp.put(r"D:\CODEX\STEPHANS OG\stephans-pet-app\restore_real_images.py", "/tmp/restore_real_images.py")
    
    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell -c /etc/odoo.conf -d Stephans --no-http --stop-after-init < /tmp/restore_real_images.py\""
    
    # Stream output
    stdin, stdout, stderr = client.exec_command(cmd)
    for line in stdout:
        print(line.strip())
    
    err = stderr.read().decode('utf-8', errors='replace')
    if err:
        print(f"STDERR: {err}")
    
    sftp.close()
    client.close()

if __name__ == "__main__":
    main()
