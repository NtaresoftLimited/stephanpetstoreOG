
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
    print("GENERATING PAW WATERMARK")
    print("="*60)

    # 1. Upload Script
    sftp = client.open_sftp()
    sftp.put("generate_paw.py", "/tmp/generate_paw.py")
    
    # 2. Run Script
    cmd = "/usr/bin/python3 /tmp/generate_paw.py"
    stdin, stdout, stderr = client.exec_command(cmd)
    
    # Check output
    print(stdout.read().decode())
    err = stderr.read().decode()
    if err:
        print(f"STDERR: {err}")
        
    # 3. Move image to static folder
    # We need to find where static folder is. Usually in custom module.
    # Let's assume /opt/odoo/custom-addons/custom_pos_reports/static/src/img/
    # We might need to create dir.
    
    print("Moving watermark to module static directory...")
    static_dir = "/opt/odoo/custom-addons/custom_pos_reports/static/src/img"
    client.exec_command(f"mkdir -p {static_dir}")
    client.exec_command(f"mv paw_watermark.png {static_dir}/paw_watermark.png")
    client.exec_command(f"chmod 644 {static_dir}/paw_watermark.png")
    
    print(f"Watermark saved to {static_dir}/paw_watermark.png")
    
    sftp.close()
    client.close()

if __name__ == "__main__":
    main()
