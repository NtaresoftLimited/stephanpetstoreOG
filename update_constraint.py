import os

file_path = r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\product_template.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Add public_categ_ids to constraint
content = content.replace("'categ_id', 'detailed_type'", "'categ_id', 'public_categ_ids', 'detailed_type'")

if 'if not record.public_categ_ids:' not in content:
    content = content.replace(
        'if not record.categ_id:\n                raise ValidationError("Category is required.")',
        'if not record.categ_id:\n                raise ValidationError("Category is required.")\n            if not record.public_categ_ids:\n                raise ValidationError("Website Categories are required.")'
    )

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print('Updated constraint in product_template.py')
