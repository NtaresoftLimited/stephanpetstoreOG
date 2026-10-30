#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

def main():
    print(f"Checking Image Attachments on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)
    
    # Check where images are stored (db or file) and sample paths
    script = """
print("STORAGE:", env['ir.config_parameter'].sudo().get_param('ir_attachment.location'))
attachments = env['ir.attachment'].search([('res_model', '=', 'product.template'), ('mimetype', 'like', 'image/%')], limit=5)
print(f"FOUND {len(attachments)} product images.")
for a in attachments:
    print(f"ID: {a.id}, Name: {a.name}, Store Fname: {a.store_fname}, File Size: {a.file_size}")
"""
    cmd = f"su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell -c /etc/odoo.conf -d Stephans --no-http --stop-after-init <<< '{script}'\""
    
    stdin, stdout, stderr = client.exec_command(cmd)
    output = stdout.read().decode('utf-8', errors='replace')
    print(output)
    
    client.close()

if __name__ == "__main__":
    main()
