import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py', 'r', encoding='utf-8') as f:
    code = f.read()

bad_str = """        message = f"📊 *{report_label} Sales Report*

Here is the sales report for {self.date_start_only} to {self.date_end_only}.
Please find the PDF attached." """

good_str = """        message = f\"\"\"📊 *{report_label} Sales Report*

Here is the sales report for {self.date_start_only} to {self.date_end_only}.
Please find the PDF attached.\"\"\" """

code = code.replace(bad_str, good_str)

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Fixed message string.")
