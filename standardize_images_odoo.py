import base64
import io
import logging
from PIL import Image, ImageOps 
try:
    from PIL import WebPImagePlugin 
except ImportError:
    pass

# Configure logging to stdout so we see it in the SSH output
logging.basicConfig(level=logging.INFO)
_logger = logging.getLogger(__name__)

def standardize_image(image_b64):
    if not image_b64:
        return False
    try:
        # Decode
        image_data = base64.b64decode(image_b64)
        img = Image.open(io.BytesIO(image_data))
        
        # Convert to RGB (handle RGBA/P properly)
        if img.mode != 'RGB':
            img = img.convert('RGB')

        # Target size
        target_size = (1024, 1024)
        
        # Create new white background image
        new_img = Image.new("RGB", target_size, (255, 255, 255))
        
        # Resize original keeping aspect ratio (contain)
        if hasattr(Image, 'Resampling'):
            resample_method = Image.Resampling.LANCZOS
        else:
            resample_method = Image.LANCZOS
            
        img.thumbnail(target_size, resample_method)
        
        # Paste centered
        x = (target_size[0] - img.width) // 2
        y = (target_size[1] - img.height) // 2
        new_img.paste(img, (x, y))
        
        # Save to buffer as optimized JPEG
        buffer = io.BytesIO()
        new_img.save(buffer, format="JPEG", quality=85, optimize=True)
        return base64.b64encode(buffer.getvalue())
    except Exception as e:
        print(f"Error processing image: {e}")
        return False

print("\n" + "="*50)
print("STARTING IMAGE STANDARDIZATION (1024x1024 White BG)")
print("="*50)

# Search for products with images
products = env['product.template'].search([('image_1920', '!=', False)])
total = len(products)
print(f"Found {total} products with images to process.")

count = 0
processed = 0
errors = 0

for p in products:
    try:
        # Only process if image exists (double check)
        if not p.image_1920:
            continue
            
        new_b64 = standardize_image(p.image_1920)
        if new_b64:
            p.write({'image_1920': new_b64})
            processed += 1
            
            # Commit every 10 records to avoid long transactions
            if processed % 10 == 0:
                env.cr.commit()
                print(f"Standardized {processed}/{total} images...")
        else:
            errors += 1
            print(f"Skipping {p.name} due to processing error.")
            
    except Exception as e:
        print(f"Error updating product {p.name}: {e}")
        errors += 1
    
    count += 1

# Final commit
env.cr.commit()
print("\n" + "="*50)
print(f"DONE. Standardized {processed} images.")
print(f"Errors: {errors}")
print("="*50)
