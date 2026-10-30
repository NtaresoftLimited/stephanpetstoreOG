#!/usr/bin/env python3
import paramiko
import sys
import io

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"
DB = "Stephans"

def main():
    print(f"Checking brands on {HOST}...")
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD, timeout=10)

    # Python script to run inside Odoo shell
    odoo_script = """
print('Checking product.brand model...')
if 'product.brand' in env:
    print('✅ product.brand model exists.')
    brands = env['product.brand'].search([])
    print(f'Found {len(brands)} brands.')
    for brand in brands:
        print(f' - {brand.name} (ID: {brand.id})')
        
    beeno = env['product.brand'].search([('name', 'ilike', 'Beeno')], limit=1)
    if beeno:
        print(f'✅ Found Beeno brand: {beeno.name} (ID: {beeno.id})')
    else:
        print('❌ Beeno brand NOT found.')
else:
    print('❌ product.brand model DOES NOT exist.')

print('Checking products...')
bello = env['product.template'].search([('name', 'ilike', 'Bello')], limit=5)
if bello:
    print(f'✅ Found {len(bello)} products matching Bello:')
    for p in bello:
        print(f' - {p.name} (ID: {p.id}, Brand: {p.brand_id.name if "brand_id" in p else "No brand field"})')
else:
    print('❌ Product Bello NOT found.')
"""
    
    # Escape quotes for bash
    odoo_script_escaped = odoo_script.replace('"', '\\"').replace("'", "\\'")

    # Construct command
    # We use a heredoc or just pass it differently to avoid complex escaping issues
    # But simple way: write to /tmp/check_brands.py and run it
    
    create_script_cmd = f"cat <<EOF > /tmp/check_brands.py\n{odoo_script}\nEOF"
    client.exec_command(create_script_cmd)
    
    cmd = f"su - odoo -c \"/usr/bin/python3 /opt/odoo/odoo-server/odoo-bin shell -c /etc/odoo.conf -d {DB} --no-http --stop-after-init < /tmp/check_brands.py\""
    
    print("Running Odoo shell script...")
    stdin, stdout, stderr = client.exec_command(cmd)
    
    output = stdout.read().decode('utf-8', errors='replace')
    error_output = stderr.read().decode('utf-8', errors='replace')
    
    print(output)
    if error_output:
        print("STDERR:", error_output)

    client.close()

if __name__ == "__main__":
    main()
