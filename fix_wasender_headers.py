import re

# Fix pos_details.py
pos_path = r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py'
with open(pos_path, 'r', encoding='utf-8') as f:
    pos_content = f.read()

pos_content = pos_content.replace(
'''        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 99fdd082b088ec50a4461bd03796de7e9a892770feddb7d8f0ed6e800e126856",
        }''',
'''        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 99fdd082b088ec50a4461bd03796de7e9a892770feddb7d8f0ed6e800e126856",
            "User-Agent": "Odoo/18.0"
        }''')

# Add raise_for_status
pos_content = pos_content.replace(
'''        try:
            requests.post(url, json=payload, headers=headers, timeout=15)
        except Exception as e:''',
'''        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
        except Exception as e:''')

with open(pos_path, 'w', encoding='utf-8') as f:
    f.write(pos_content)


# Fix product_template.py
prod_path = r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\product_template.py'
with open(prod_path, 'r', encoding='utf-8') as f:
    prod_content = f.read()

prod_content = prod_content.replace(
'''            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer 99fdd082b088ec50a4461bd03796de7e9a892770feddb7d8f0ed6e800e126856",
            }''',
'''            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer 99fdd082b088ec50a4461bd03796de7e9a892770feddb7d8f0ed6e800e126856",
                "User-Agent": "Odoo/18.0"
            }''')

prod_content = prod_content.replace(
'''                    requests.post(url, json=payload, headers=headers, timeout=10)
        except Exception as e:''',
'''                    resp = requests.post(url, json=payload, headers=headers, timeout=10)
                    resp.raise_for_status()
        except Exception as e:''')

with open(prod_path, 'w', encoding='utf-8') as f:
    f.write(prod_content)

print("Files fixed locally.")
