
import paramiko
import sys

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
        
        print(">>> Checking /etc/odoo.conf:")
        stdin, stdout, stderr = client.exec_command("cat /etc/odoo.conf")
        print(stdout.read().decode('utf-8'))
        
        print("\n>>> Searching for 'grooming' directories:")
        stdin, stdout, stderr = client.exec_command("find / -type d -name grooming 2>/dev/null")
        print(stdout.read().decode('utf-8'))

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
