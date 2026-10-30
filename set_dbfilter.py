#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Setting dbfilter on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    sftp = client.open_sftp()

    # Read current config
    with sftp.open('/etc/odoo.conf', 'r') as f:
        config = f.read().decode('utf-8')
    
    # Check if dbfilter already exists
    if 'dbfilter' not in config:
        print(">>> Adding dbfilter to config...")
        # Add dbfilter to auto-select Stephans database
        new_config = config + "\n# Auto-select Stephans database\ndbfilter = ^Stephans$\nlist_db = True\n"
        
        with sftp.open('/etc/odoo.conf', 'w') as f:
            f.write(new_config)
        print("   Done!")
    else:
        print(">>> dbfilter already configured")

    # Restart Odoo
    print(">>> Restarting Odoo...")
    stdin, stdout, stderr = client.exec_command("systemctl restart odoo && sleep 3 && systemctl is-active odoo")
    print(stdout.read().decode('utf-8', errors='replace').strip())

    # Test web access
    print("\n>>> Testing web access...")
    stdin, stdout, stderr = client.exec_command("curl -sI http://127.0.0.1:8069/web/login | head -5")
    print(stdout.read().decode('utf-8', errors='replace').strip())

    sftp.close()
    client.close()
    
    print("\n" + "="*60)
    print("CONFIGURATION COMPLETE!")
    print("="*60)
    print("Database: Stephans (auto-selected)")
    print("URL: http://166.1.227.63:8069/web/login")
    print("="*60)

if __name__ == "__main__":
    main()
