import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Just replace the exact start and end
code = re.sub(
    r'message = f"📊 \*{report_label} Sales Report\*.*?Please find the PDF attached\."',
    'message = f"""📊 *{report_label} Sales Report*\\n\\nHere is the sales report for {self.date_start_only} to {self.date_end_only}.\\nPlease find the PDF attached."""',
    code,
    flags=re.DOTALL
)

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Fixed message string via regex.")
