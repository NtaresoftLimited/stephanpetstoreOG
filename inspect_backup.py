import zipfile
import os

zip_path = r"D:\CODEX\STEPHANS OG\stephans-pet-app\Stephans_2026-01-27_12-19-23.zip"

if not os.path.exists(zip_path):
    print(f"ERROR: File not found at {zip_path}")
    exit(1)

print(f"Inspecting {zip_path}...")
try:
    with zipfile.ZipFile(zip_path, 'r') as z:
        # List first 20 items to guess structure
        print("\n--- First 20 Files ---")
        for i, info in enumerate(z.infolist()):
            if i >= 20: break
            print(f"{info.filename} ({info.file_size} bytes)")
            
        # Check for filestore
        filestore_files = [f for f in z.namelist() if 'filestore' in f]
        print(f"\n--- Filestore Stats ---")
        print(f"Total filestore files: {len(filestore_files)}")
        if filestore_files:
            print(f"Sample paths: {filestore_files[:5]}")
            
except Exception as e:
    print(f"Error inspecting zip: {e}")
