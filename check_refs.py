#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking XML refs on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # Use odoo shell to check refs
    script = """
print("CHECK_MENU:", env.ref("point_of_sale.menu_point_of_sale_report", raise_if_not_found=False))
print("CHECK_VIEW:", env.ref("point_of_sale.view_pos_details_wizard", raise_if_not_found=False))
print("CHECK_ACTION:", env.ref("point_of_sale.action_report_pos_details", raise_if_not_found=False))
"""
    cmd = f"su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell -c /etc/odoo.conf -d Stephans --no-http --stop-after-init <<< '{script}'\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='replace')
    print(output)

    client.close()

if __name__ == "__main__":
    main()
