import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\controllers\pdf_report_controller.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace('GREEN = HexColor("#173d31")', 'GREEN = HexColor("#3e220f")')
code = code.replace('ACCENT = HexColor("#00a86b")', 'ACCENT = HexColor("#3e220f")')

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\controllers\pdf_report_controller.py', 'w', encoding='utf-8') as f:
    f.write(code)
