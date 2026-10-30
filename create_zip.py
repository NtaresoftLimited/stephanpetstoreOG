import zipfile
import os

def zip_dir(path, ziph):
    # ziph is zipfile handle
    for root, dirs, files in os.walk(path):
        for file in files:
            file_path = os.path.join(root, file)
            arcname = os.path.relpath(file_path, os.path.dirname(path))
            ziph.write(file_path, arcname)

dir_to_zip = r"D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports"
zip_file = r"D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports.zip"

print(f"Zipping {dir_to_zip} to {zip_file}...")
with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
    zip_dir(dir_to_zip, zipf)
print("Done!")
