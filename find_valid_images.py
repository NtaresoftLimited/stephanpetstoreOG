print("--- FIND VALID IMAGES ---")
products = env['product.template'].search([('image_1920', '!=', False)], limit=5)
for p in products:
    print(f"Product: {p.name} (ID: {p.id})")
    print(f"Data Len: {len(p.image_1920)}")
