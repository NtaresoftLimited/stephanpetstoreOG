#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Deep Inspect Bioline on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    
    script = """
p = env['product.template'].search([('name', 'ilike', 'Bioline Tea Tree')], limit=1)
if p:
    print(f"Product: {p.name} (ID: {p.id})")
    print(f"Image 1920 (First 50b): {p.image_1920[:50] if p.image_1920 else 'None'}")
    
    # Check attachments explicitly linked to this ID
    atts = env['ir.attachment'].search([('res_model', '=', 'product.template'), ('res_id', '=', p.id)])
    print(f"Attachments found: {len(atts)}")
    for a in atts:
        print(f" - ID: {a.id}, Name: {a.name}, Field: {a.res_field}, Type: {a.type}, Store: {a.store_fname}")
else:
    print("Product not found.")
"""
    cmd = f"su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell -c /etc/odoo.conf -d Stephans --no-http --stop-after-init <<< '{script}'\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='replace')
    print(output)
    
    client.close()

if __name__ == "__main__":
    main()
