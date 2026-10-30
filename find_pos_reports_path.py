
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Connecting to {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    print("\n" + "="*60)
    print("FINDING custom_pos_reports PATH")
    print("="*60)

    cmd = "find /opt/odoo -type d -name custom_pos_reports 2>/dev/null"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    paths = stdout.read().decode().strip().split('\n')
    for p in paths:
        if p:
            print(f"Found: {p}")
            
    client.close()

if __name__ == "__main__":
    main()
