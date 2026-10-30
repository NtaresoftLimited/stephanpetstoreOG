import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\__manifest__.py', 'r', encoding='utf-8') as f:
    code = f.read()

if "'data/cron.xml'," not in code:
    code = code.replace("'views/pos_details_views.xml',", "'data/cron.xml',\n        'views/pos_details_views.xml',")
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\__manifest__.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("SUCCESS")
else:
    print("Already added")
