import os

def replace_in_file(filepath, old, new):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    if old in content:
        content = content.replace(old, new)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Replaced in {filepath}")
    else:
        print(f"'{old}' not found in {filepath}")

base_path = r"D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports"

replace_in_file(os.path.join(base_path, 'reports', 'a4_template.xml'), 'Total Cash Out:', 'Total Expenses:')
replace_in_file(os.path.join(base_path, 'reports', 'thermal_template.xml'), 'Total Cash Out:', 'Total Expenses:')
replace_in_file(os.path.join(base_path, 'wizard', 'pos_details.py'), 'Total Cash Out (TSh):', 'Total Expenses (TSh):')
