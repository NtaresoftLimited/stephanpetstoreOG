print("--- REGENERATING IMAGES ---")
products = env['product.template'].search([('image_1920', '!=', False)])
print(f"Processing {len(products)} products...")

count = 0
for p in products:
    try:
        # Trigger re-write to force attachment creation
        p.write({'image_1920': p.image_1920})
        count += 1
        if count % 10 == 0:
            env.cr.commit()
            print(f"Processed {count}...")
    except Exception as e:
        print(f"Error on {p.name}: {e}")

env.cr.commit()
print(f"DONE. Regenerated {count} images.")
