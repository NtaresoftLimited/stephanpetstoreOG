import xmlrpc.client

# Odoo connection details
url = "https://erp.stephanspetstore.co.tz"
db = "Stephans"
username = "info@stephanspetstore.co.tz"
password = "Stephan@3202"

print("=" * 60)
print("FIXING POS LANGUAGE CONFIGURATION")
print("=" * 60)

try:
    # Authenticate
    print("\n[1/5] Connecting to Odoo...")
    common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
    uid = common.authenticate(db, username, password, {})
    
    if not uid:
        print("[X] Authentication failed. Please check your credentials.")
        exit(1)
    
    print(f"[OK] Connected as user ID: {uid}")
    
    models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
    
    # Find English language
    print("\n[2/5] Finding English language...")
    languages = models.execute_kw(db, uid, password,
        'res.lang', 'search_read',
        [[['code', '=', 'en_US'], ['active', '=', True]]],
        {'fields': ['id', 'name', 'code'], 'limit': 1}
    )
    
    if not languages:
        print("[X] English language not found. Please install it in Odoo first.")
        exit(1)
    
    english_id = languages[0]['id']
    print(f"[OK] Found: {languages[0]['name']} (ID: {english_id})")
    
    # Find POS config
    print("\n[3/5] Finding POS configuration...")
    pos_configs = models.execute_kw(db, uid, password,
        'pos.config', 'search_read',
        [[['name', '=', "Stephan's Pet Store"]]],
        {'fields': ['id', 'name', 'default_language_id', 'language_ids'], 'limit': 1}
    )
    
    if not pos_configs:
        print("[X] POS configuration 'Stephan's Pet Store' not found.")
        exit(1)
    
    pos_id = pos_configs[0]['id']
    pos_name = pos_configs[0]['name']
    print(f"[OK] Found: {pos_name} (ID: {pos_id})")
    print(f"   Current Default Language: {pos_configs[0].get('default_language_id')}")
    print(f"   Current Languages: {pos_configs[0].get('language_ids')}")
    
    # Update POS configuration
    print("\n[4/5] Updating POS configuration...")
    update_values = {
        'default_language_id': english_id,
        'language_ids': [(6, 0, [english_id])]  # Replace all with English only
    }
    
    result = models.execute_kw(db, uid, password,
        'pos.config', 'write',
        [[pos_id], update_values]
    )
    
    if result:
        print("[OK] Successfully updated POS configuration!")
    else:
        print("[X] Failed to update POS configuration")
        exit(1)
    
    # Verify the changes
    print("\n[5/5] Verifying changes...")
    pos_updated = models.execute_kw(db, uid, password,
        'pos.config', 'search_read',
        [[['id', '=', pos_id]]],
        {'fields': ['name', 'default_language_id', 'language_ids'], 'limit': 1}
    )
    
    if pos_updated:
        pos = pos_updated[0]
        print(f"[OK] Verified: {pos['name']}")
        print(f"   Default Language: {pos.get('default_language_id')}")
        print(f"   Languages: {pos.get('language_ids')}")
    
    print("\n" + "=" * 60)
    print("FIX COMPLETED SUCCESSFULLY!")
    print("=" * 60)
    print("\nYou can now:")
    print("  1. Refresh the POS settings page in Odoo")
    print("  2. The validation error should be gone")
    print("  3. Save your other POS settings without issues")
    print("\n")
    
except Exception as e:
    print(f"\n[X] ERROR: {str(e)}")
    print("\nPlease check:")
    print("  - Your Odoo URL, database name, username, and password")
    print("  - Network connection to Odoo server")
    print("  - User has permission to modify POS settings")
    exit(1)
