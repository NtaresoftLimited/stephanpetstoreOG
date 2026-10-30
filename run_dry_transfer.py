#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Running Dry Run on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    
    sftp = client.open_sftp()
    sftp.put(r"D:\CODEX\STEPHANS OG\stephans-pet-app\dry_run_transfer.py", "/tmp/dry_run_transfer.py")
    
    # Run as 'odoo' user generally, but for psycog2 connect to 'Stephans_Temp_Restore' which is owned by 'odoo'
    # we might need to install psycopg2 or use the one in odoo env.
    # Actually, Odoo's python environment works best.
    
    cmd = "su - odoo -c \"/usr/bin/python3 /tmp/dry_run_transfer.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='replace')
    err = stderr.read().decode('utf-8', errors='replace')
    print(output)
    if err:
        print(f"STDERR: {err}")
    
    sftp.close()
    client.close()

if __name__ == "__main__":
    main()
