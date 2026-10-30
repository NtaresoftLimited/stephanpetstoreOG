
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
    print("RUNNING LOGO COPY")
    print("="*60)

    # 1. Upload Script
    sftp = client.open_sftp()
    sftp.put("copy_logo.py", "/tmp/copy_logo.py")
    
    # 2. Run Script
    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell -c /etc/odoo.conf -d Stephans --no-http --stop-after-init < /tmp/copy_logo.py\""
    stdin, stdout, stderr = client.exec_command(cmd)
    
    for line in stdout:
        print(line.strip())
        
    err = stderr.read().decode().strip()
    if err:
        print(f"STDERR: {err}")
        
    client.close()

if __name__ == "__main__":
    main()
