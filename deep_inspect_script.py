print("--- DEEP INSPECT ---")
p = env['product.template'].search([('name', 'ilike', 'Bioline Tea Tree')], limit=1)
if p:
    print(f"Product: {p.name} (ID: {p.id})")
    print(f"Image 1920 Type: {type(p.image_1920)}")
    print(f"Image 1920 Length: {len(p.image_1920) if p.image_1920 else 0}")
    
    # Check attachments explicitly linked to this ID
    atts = env['ir.attachment'].search([('res_model', '=', 'product.template'), ('res_id', '=', p.id)])
    print(f"Attachments found: {len(atts)}")
    for a in atts:
        print(f" - ID: {a.id}, Name: {a.name}, Field: {a.res_field}, Type: {a.type}, Store: {a.store_fname}")
else:
    print("Product not found.")
print("--- END ---")
