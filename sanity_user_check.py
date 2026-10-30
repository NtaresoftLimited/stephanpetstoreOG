import xmlrpc.client
import os
import re

# Manually parse .env from StephansEcomercewithAI directory
env_path = r"d:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\.env"
env_vars = {}
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            match = re.match(r'^\s*([A-Za-z0-9_]+)\s*=\s*(.*)\s*$', line)
            if match:
                key, val = match.groups()
                env_vars[key] = val.strip()

url = env_vars.get('ODOO_URL')
db = env_vars.get('ODOO_DB')
username = env_vars.get('ODOO_USER')
password = env_vars.get('ODOO_PASSWORD')

def check_sanity():
    print(f"Connecting to {url}...")
    try:
        common = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/common')
        uid = common.authenticate(db, username, password, {})
        
        if not uid:
            print("Authentication FAILED: Invalid credentials.")
            return

        print(f"Authentication SUCCESSFUL. UID: {uid}")
        
        models = xmlrpc.client.ServerProxy(f'{url}/xmlrpc/2/object')
        
        # 1. User Info
        user_data = models.execute_kw(db, uid, password, 'res.users', 'read', [uid], {'fields': ['name', 'login', 'company_id', 'groups_id', 'active']})
        user = user_data[0]
        print(f"\nUser Profile:")
        print(f"  Name: {user['name']}")
        print(f"  Login: {user['login']}")
        print(f"  Active: {user['active']}")
        print(f"  Company: {user['company_id'][1]} (ID: {user['company_id'][0]})")

        # 2. Permissions / Groups
        groups = models.execute_kw(db, uid, password, 'res.groups', 'read', [user['groups_id']], {'fields': ['full_name', 'category_id']})
        print(f"\nSignificant Access Rights:")
        critical_keywords = ['Admin', 'Manager', 'Point of Sale', 'Inventory', 'Stock', 'Account']
        held_rights = []
        for g in groups:
            if any(kw.lower() in g['full_name'].lower() for kw in critical_keywords):
                held_rights.append(g['full_name'])
        
        for right in sorted(held_rights):
            print(f"  - {right}")

        # 3. Quick module access test
        try:
            pos_configs = models.execute_kw(db, uid, password, 'pos.config', 'search_count', [[]])
            print(f"\nPOS Access Verified: Found {pos_configs} POS configurations.")
        except Exception as e:
            print(f"\nPOS Access Issues: {e}")

        try:
            stock_picks = models.execute_kw(db, uid, password, 'stock.picking', 'search_count', [[]])
            print(f"Inventory Access Verified: Found {stock_picks} stock operations.")
        except Exception as e:
            print(f"Inventory Access Issues: {e}")

    except Exception as e:
        print(f"ERROR connecting to Odoo: {e}")

if __name__ == "__main__":
    check_sanity()
