import xmlrpc.client
import os
from dotenv import load_dotenv

load_dotenv()

# Odoo connection details
url = os.getenv('ODOO_URL', 'https://erp.example.com')
db = os.getenv('ODOO_DB', 'your_database')
username = os.getenv('ODOO_USER', 'admin@example.com')
password = os.getenv('ODOO_PASSWORD', 'your_password')

# Authenticate
common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
uid = common.authenticate(db, username, password, {})
models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')

print(f"Connected to Odoo as user ID: {uid}")

# Find the POS config
pos_configs = models.execute_kw(db, uid, password,
    'pos.config', 'search_read',
    [[['name', '=', "Stephan's Pet Store"]]],
    {'fields': ['id', 'name', 'default_language_id', 'language_ids']}
)

if pos_configs:
    for pos in pos_configs:
        print(f"\nPOS Config: {pos['name']} (ID: {pos['id']})")
        print(f"Default Language ID: {pos.get('default_language_id')}")
        print(f"Language IDs: {pos.get('language_ids')}")
else:
    print("No POS config found for Stephan's Pet Store")

# Get available languages in the system
languages = models.execute_kw(db, uid, password,
    'res.lang', 'search_read',
    [[['active', '=', True]]],
    {'fields': ['id', 'name', 'code']}
)

print("\n=== Available Languages in System ===")
for lang in languages:
    print(f"ID: {lang['id']} | Name: {lang['name']} | Code: {lang['code']}")

# Fix: Set English as default language and clear language_ids
if pos_configs:
    pos_id = pos_configs[0]['id']
    
    # Find English language
    english = [l for l in languages if l['code'] == 'en_US']
    
    if english:
        english_id = english[0]['id']
        print(f"\n=== Fixing POS Configuration ===")
        print(f"Setting default language to: {english[0]['name']} (ID: {english_id})")
        
        # Update the POS config
        try:
            models.execute_kw(db, uid, password,
                'pos.config', 'write',
                [[pos_id], {
                    'default_language_id': english_id,
                    'language_ids': [(6, 0, [english_id])]  # Replace all with English
                }]
            )
            print("✅ Successfully updated POS configuration!")
            print(f"Default language set to: English (ID: {english_id})")
            print(f"Available languages set to: [English]")
            
        except Exception as e:
            print(f"❌ Error updating POS config: {e}")
    else:
        print("❌ English language not found in system")
        print("Please install English language first in Odoo Settings > Translations > Languages")
else:
    print("❌ Cannot fix - POS config not found")

print("\n=== Verification ===")
# Verify the fix
pos_configs_after = models.execute_kw(db, uid, password,
    'pos.config', 'search_read',
    [[['name', '=', "Stephan's Pet Store"]]],
    {'fields': ['id', 'name', 'default_language_id', 'language_ids']}
)

if pos_configs_after:
    pos = pos_configs_after[0]
    print(f"POS Config: {pos['name']}")
    print(f"Default Language ID: {pos.get('default_language_id')}")
    print(f"Language IDs: {pos.get('language_ids')}")
    print("\n✓ You should now be able to save the POS settings without errors!")
