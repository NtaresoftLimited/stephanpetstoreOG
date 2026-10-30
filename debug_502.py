
import paramiko
import sys
import time

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
        
        # 1. Check Service Status
        print("\n>>> Checking Odoo Service Status...")
        stdin, stdout, stderr = client.exec_command("systemctl status odoo")
        print(stdout.read().decode())
        
        # 2. Check log file directly (if it exists)
        print("\n>>> Tailing /var/log/odoo/odoo.log (last 100 lines)...")
        stdin, stdout, stderr = client.exec_command("tail -n 100 /var/log/odoo/odoo.log")
        out = stdout.read().decode()
        if out:
            print(out)
        else:
            print("(Log file empty or not accessible, checking journalctl...)")
            stdin, stdout, stderr = client.exec_command("journalctl -u odoo --no-pager -n 50")
            print(stdout.read().decode())

        # 3. Check processes
        print("\n>>> Checking running odoo-bin processes...")
        stdin, stdout, stderr = client.exec_command("ps aux | grep odoo-bin")
        print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
