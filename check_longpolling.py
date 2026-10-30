#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking and fixing Odoo longpolling on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # Check current config
    print("\n>>> Current Odoo Config:")
    stdin, stdout, stderr = client.exec_command("cat /etc/odoo.conf")
    print(stdout.read().decode('utf-8', errors='replace'))

    # Check Odoo logs for errors
    print("\n>>> Recent Odoo Logs:")
    stdin, stdout, stderr = client.exec_command("tail -30 /var/log/odoo/odoo.log")
    print(stdout.read().decode('utf-8', errors='replace'))

    # Check if gevent is installed
    print("\n>>> Checking gevent installation:")
    stdin, stdout, stderr = client.exec_command("pip3 show gevent 2>&1 || python3 -c 'import gevent; print(gevent.__version__)' 2>&1")
    out = stdout.read().decode('utf-8', errors='replace')
    print(out)
    
    if "not found" in out.lower() or "no module" in out.lower():
        print("\n>>> Installing gevent...")
        stdin, stdout, stderr = client.exec_command("pip3 install gevent")
        print(stdout.read().decode('utf-8', errors='replace'))

    client.close()

if __name__ == "__main__":
    main()
