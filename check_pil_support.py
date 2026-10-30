
import PIL
from PIL import Image, features

print(f"PIL Version: {PIL.__version__}")
try:
    print(f"WebP support: {features.check('webp')}")
except:
    print("Could not check WebP support via features.")

print("--- REGISTERED EXTENSIONS ---")
Image.init()
print(f"WEBP in extensions: {'WEBP' in Image.EXTENSION or '.webp' in Image.EXTENSION}")
print(f"MIME types: {Image.MIME.get('WEBP')}")
