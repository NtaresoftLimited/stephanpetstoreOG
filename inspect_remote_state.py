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
        
        print("\n>>> Checking /etc/odoo.conf:")
        stdin, stdout, stderr = client.exec_command("cat /etc/odoo.conf")
        print(stdout.read().decode())
        
        print("\n>>> Checking custom-addons directory content:")
        stdin, stdout, stderr = client.exec_command("ls -la /opt/odoo/custom-addons")
        print(stdout.read().decode())

        print("\n>>> Checking whatsapp_connector content:")
        stdin, stdout, stderr = client.exec_command("ls -la /opt/odoo/custom-addons/whatsapp_connector")
        print(stdout.read().decode())
        
        print("\n>>> Checking Odoo Log (last 50 lines):")
        # Trying common log locations
        cmd = "tail -n 50 /var/log/odoo/odoo-server.log"
        stdin, stdout, stderr = client.exec_command(cmd)
        print(stdout.read().decode())
        print(stderr.read().decode())

    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    main()
