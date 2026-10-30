import os
import re

file_path = r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# find def action_download_custom_pdf and replace to EOF
idx = content.find('def action_download_custom_pdf')
if idx != -1:
    content = content[:idx] + '''def action_download_custom_pdf(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': f'/print/transfer/{self.id}',
            'target': 'new',
        }
'''

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
