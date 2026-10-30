import os

file_path = r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\product_template.py'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip_next = False
for line in lines:
    if skip_next:
        skip_next = False
        continue
    
    # Remove it from the constrains decorator
    if "@api.constrains" in line and "'public_categ_ids'," in line:
        line = line.replace("'public_categ_ids', ", "")
        
    # Remove the validation block
    if "if not record.public_categ_ids:" in line:
        skip_next = True # Skip the next line which is the raise ValidationError
        continue
        
    new_lines.append(line)

with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
