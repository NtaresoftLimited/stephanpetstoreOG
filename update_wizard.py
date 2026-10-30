import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\wizard\whatsapp_transfer_wizard.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_logic = """            phone = picking.partner_id.mobile or picking.partner_id.phone
            if phone:
                phone_cleaned = ''.join(filter(str.isdigit, phone))
                res['phone_number'] = phone_cleaned"""

new_logic = """            # Default to the requested automatic reporting number
            res['phone_number'] = '+255792079463'"""

code = code.replace(old_logic, new_logic)

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\wizard\whatsapp_transfer_wizard.py', 'w', encoding='utf-8') as f:
    f.write(code)
