import os
import re

base_dir = r'D:\CODEX\STEPHANS OG\stephans-pet-app'
modified_files = []

for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Replace '+255792079463' or '+255792079463' globally
                new_content = re.sub(r"['\"]255792079463['\"]", "'+255792079463'", content)
                
                if new_content != content:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    modified_files.append(filepath)
            except Exception as e:
                pass

print('Modified Files:')
for mf in modified_files:
    print(mf)
