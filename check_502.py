import paramiko
import sys

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    
    with open('odoo_diag.txt', 'wb') as f:
        f.write(b"Checking Odoo service status...\n")
        stdin, stdout, stderr = client.exec_command("systemctl status odoo --no-pager")
        f.write(stdout.read())
        
        f.write(b"\nRestarting Odoo service...\n")
        stdin, stdout, stderr = client.exec_command("systemctl restart odoo")
        f.write(stdout.read())
        f.write(stderr.read())
        
        f.write(b"\nChecking Odoo service status after restart...\n")
        stdin, stdout, stderr = client.exec_command("systemctl status odoo --no-pager")
        f.write(stdout.read())

        f.write(b"\nChecking last 50 lines of Odoo log...\n")
        stdin, stdout, stderr = client.exec_command("tail -n 50 /var/log/odoo/odoo-server.log")
        f.write(stdout.read())

    client.close()
    print("Diagnostics complete, written to odoo_diag.txt")

if __name__ == "__main__":
    main()
