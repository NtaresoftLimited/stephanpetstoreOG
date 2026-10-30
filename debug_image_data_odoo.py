
import base64
import io

print("--- DEBUGGING IMAGE DATA ---")
product = env['product.template'].search([('image_1920', '!=', False)], limit=1)

if not product:
    print("No products with images found.")
else:
    print(f"Product: {product.name}")
    data = product.image_1920
    print(f"Type: {type(data)}")
    print(f"Length: {len(data)}")
    print(f"First 50 chars: {data[:50]}")
    
    # Try decoding
    try:
        decoded = base64.b64decode(data)
        print(f"Decoded length: {len(decoded)}")
        print(f"Decoded first 20 bytes: {decoded[:20]}")
    except Exception as e:
        print(f"Base64 decode error: {e}")

print("--- DONE ---")
