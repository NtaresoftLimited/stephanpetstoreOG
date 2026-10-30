import os

file_path = r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace("\\'type\\'", "'type'")
content = content.replace("\\'ir.actions.act_url\\'", "'ir.actions.act_url'")
content = content.replace("\\'url\\'", "'url'")
content = content.replace("f\\'print", "f'/print")
content = content.replace("{self.id}\\'", "{self.id}'")
content = content.replace("f\\'/print/transfer/{self.id}\\'", "f'/print/transfer/{self.id}'")
content = content.replace("\\'target\\'", "'target'")
content = content.replace("\\'new\\'", "'new'")

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
