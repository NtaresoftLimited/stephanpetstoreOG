import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Replace: pdf_content, _ = report._render_qweb_pdf(self.ids)
# With:    pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf('custom_pos_reports.action_report_pos_a4', res_ids=self.ids)

old_line = "pdf_content, _ = report._render_qweb_pdf(self.ids)"
new_line = "pdf_content, _ = self.env['ir.actions.report']._render_qweb_pdf('custom_pos_reports.action_report_pos_a4', res_ids=self.ids)"

if old_line in code:
    code = code.replace(old_line, new_line)
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("SUCCESS: Fixed pos_details.py")
else:
    print("ERROR: old_line not found")
