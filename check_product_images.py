print("--- PRODUCT TABLE CHECK ---")
products = env['product.template'].search([('image_1920', '!=', False)], limit=5)
print(f"Products with image_1920 data: {len(products)}")

print("\n--- SAMPLE PRODUCT ---")
p = env['product.template'].search([], limit=1)
if p:
    print(f"Name: {p.name}")
    print(f"Has Image 1920? {bool(p.image_1920)}")
    print(f"Has Image 128? {bool(p.image_128)}")
else:
    print("No products found.")
