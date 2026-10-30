
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
    client.connect(HOST, username=USER, password=PASSWORD, timeout=300)

    print("\n" + "="*60)
    print("RUNNING IMAGE STANDARDIZATION ON SERVER")
    print("="*60)

    # 1. Upload Script
    print("\n>> Uploading script to /tmp/standardize_images.py...")
    sftp = client.open_sftp()
    sftp.put("standardize_images_odoo.py", "/tmp/standardize_images.py")
    sftp.close()

    # 2. Run Script via Odoo Shell
    print("\n>> Executing Odoo Shell Script...")
    # Using the same command structure as run_regen.py
    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell -c /etc/odoo.conf -d Stephans --no-http --stop-after-init < /tmp/standardize_images.py\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Stream Output
    for line in stdout:
        line = line.strip()
        if line:
            print(line)
            
    # Check Errors
    err_output = stderr.read().decode().strip()
    if err_output:
        print("\nSTDERR:") 
        print(err_output)

    client.close()
    print("\nScript Execution Complete.")

if __name__ == "__main__":
    main()
