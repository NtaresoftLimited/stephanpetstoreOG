import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\product_template.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_block = '''                    product_name = record.name or 'Unknown Product'
                    message = f"🔔 *New Product Needs Approval*\\n\\nA new product '{product_name}' has been created in Odoo.\\nIt is currently blocked from sales and inventory until you review and Approve it."
                    
                    payload = {'''

new_block = '''                    product_name = record.name or 'Unknown Product'
                    base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
                    product_link = f"{base_url}/web#id={record.id}&model=product.template&view_type=form"
                    
                    message = f"🔔 *New Product Needs Approval*\\n\\nA new product '{product_name}' has been created in Odoo.\\nIt is currently blocked from sales and inventory until you review and Approve it.\\n\\n👉 *Click here to review and approve:* \\n{product_link}"
                    
                    payload = {'''

if old_block in code:
    code = code.replace(old_block, new_block)
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\product_template.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("SUCCESS")
else:
    print("ERROR: block not found")
