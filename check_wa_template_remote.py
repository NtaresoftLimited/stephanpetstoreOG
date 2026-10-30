#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking model 'whatsapp.template' on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # Use odoo shell to check model and list fields
    cmd = "su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell -c /etc/odoo.conf -d Stephans --no-http --stop-after-init <<< 'print(\\\"MODEL_CHECK:\\\", \\\"whatsapp.template\\\" in env); print(\\\"FIELDS:\\\", env[\\\"whatsapp.template\\\"].fields_get().keys() if \\\"whatsapp.template\\\" in env else \\\"None\\\")'\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='replace')
    print(output)
    
    client.close()

if __name__ == "__main__":
    main()
