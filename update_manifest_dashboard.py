import paramiko
import ast
import pprint

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "yCiEf6P2c,soWK"

MANIFEST_PATH = "/opt/odoo/custom-addons/custom_pos_reports/__manifest__.py"

def main():
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST, username=USER, password=PASSWORD)
    sftp = client.open_sftp()
    
    print("Updating Manifest...")
    
    # Read manifest
    with sftp.file(MANIFEST_PATH, "r") as f:
        content = f.read().decode()
    
    # Parse dict
    manifest = ast.literal_eval(content)
    
    # 1. Update data
    if 'data' not in manifest:
        manifest['data'] = []
    
    new_data = 'views/dashboard_action.xml'
    if new_data not in manifest['data']:
        manifest['data'].append(new_data)
        print(f"Added {new_data} to data")

    # 2. Update assets
    if 'assets' not in manifest:
        manifest['assets'] = {}
        
    if 'web.assets_backend' not in manifest['assets']:
        manifest['assets']['web.assets_backend'] = []
        
    new_assets = [
        'custom_pos_reports/static/src/js/dashboard.js',
        'custom_pos_reports/static/src/xml/dashboard.xml'
    ]
    
    for asset in new_assets:
        if asset not in manifest['assets']['web.assets_backend']:
            manifest['assets']['web.assets_backend'].append(asset)
            print(f"Added {asset} to web.assets_backend")

    # Write back
    # Use pprint for nice formatting
    new_content = pprint.pformat(manifest, indent=4, width=100)
    
    with sftp.file(MANIFEST_PATH, "w") as f:
        f.write(new_content)
    
    print("Manifest updated successfully.")
    
    sftp.close()
    client.close()

if __name__ == "__main__":
    main()
