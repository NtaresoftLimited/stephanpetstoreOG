
import paramiko
import sys

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        print(f"Connecting to {HOST}...")
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
        
        # 1. Check Odoo Configuration for Log Path
        print("\n>>> Reading /etc/odoo.conf...")
        stdin, stdout, stderr = client.exec_command("cat /etc/odoo.conf")
        conf_content = stdout.read().decode().strip()
        print(conf_content)
        
        log_path = "/var/log/odoo/odoo-server.log" # Default guess
        for line in conf_content.split('\n'):
            if line.strip().startswith("logfile"):
                log_path = line.split("=")[1].strip()
                print(f"\nFound configured log path: {log_path}")
                break
        
        # 2. Check Service Status
        print("\n>>> Checking Service Status...")
        stdin, stdout, stderr = client.exec_command("systemctl status odoo --no-pager")
        print(stdout.read().decode())
        
        # 3. Fetch Last 100 Lines of Log
        print(f"\n>>> Fetching last 100 lines of {log_path}...")
        stdin, stdout, stderr = client.exec_command(f"tail -n 100 {log_path}")
        log_content = stdout.read().decode()
        if log_content:
            print(log_content)
        else:
            print(f"Log file empty or not found. Stderr: {stderr.read().decode()}")

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
