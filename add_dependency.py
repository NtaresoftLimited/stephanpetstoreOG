import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\__manifest__.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add 'product_auto_code' to the depends list if not already there
if "'product_auto_code'" not in code:
    old_depends = """    'depends': [
        'base',
        'calendar',
        'mail',
        'sale_management',
        'account',
        'whatsapp_connector',
        'point_of_sale',
        'pos_sale',
        'pos_discount',
        'pos_loyalty',
        'stock',
    ],"""
    new_depends = """    'depends': [
        'base',
        'calendar',
        'mail',
        'sale_management',
        'account',
        'whatsapp_connector',
        'point_of_sale',
        'pos_sale',
        'pos_discount',
        'pos_loyalty',
        'stock',
        'product_auto_code',
    ],"""
    
    code = code.replace(old_depends, new_depends)
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\__manifest__.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("SUCCESS: grooming manifest updated.")
else:
    print("Already added to grooming.")
