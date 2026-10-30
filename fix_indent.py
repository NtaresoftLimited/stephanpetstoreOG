import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace("def action_print_a4(self):\n        # Calls the QWeb PDF (A4)", "    def action_print_a4(self):\n        # Calls the QWeb PDF (A4)")

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Fixed indentation.")
