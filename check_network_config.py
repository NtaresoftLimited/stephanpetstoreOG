
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
        
        # 1. Odoo Config
        print("\n>>> /etc/odoo.conf:")
        stdin, stdout, stderr = client.exec_command("cat /etc/odoo.conf")
        print(stdout.read().decode())
        
        # 2. Listening Ports
        print("\n>>> Listening Ports (ss -tuln):")
        stdin, stdout, stderr = client.exec_command("ss -tulnp | grep python")
        print(stdout.read().decode())
        
        # 3. Nginx Config
        print("\n>>> Nginx Configs:")
        stdin, stdout, stderr = client.exec_command("ls /etc/nginx/sites-enabled/")
        files = stdout.read().decode().splitlines()
        for f in files:
            if f:
                print(f"--- /etc/nginx/sites-enabled/{f} ---")
                stdin, stdout, stderr = client.exec_command(f"cat /etc/nginx/sites-enabled/{f}")
                print(stdout.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
