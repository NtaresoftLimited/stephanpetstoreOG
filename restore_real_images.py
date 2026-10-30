import psycopg2
import os
import base64

# 1. Connect to Source (Temp DB)
conn = psycopg2.connect("dbname=Stephans_Temp_Restore user=odoo")
cur = conn.cursor()

# 2. Query for ALL product images
query = """
    SELECT pt.default_code, pt.name, att.store_fname
    FROM product_template pt
    JOIN ir_attachment att ON att.res_model = 'product.template' 
                           AND att.res_field = 'image_1920' 
                           AND att.res_id = pt.id
    WHERE att.store_fname IS NOT NULL;
"""
cur.execute(query)
rows = cur.fetchall()
print(f"Total images to restore: {len(rows)}")

# 3. Process each image
count = 0
errors = 0
for row in rows:
    ref, name, fname = row
    
    fpath = f"/tmp/restore_data/filestore/{fname}"
    if not os.path.exists(fpath):
        #print(f"Skipping {name}: File not found at {fpath}")
        continue
        
    try:
        # Read file binary
        with open(fpath, 'rb') as f:
            img_data = f.read()
            b64_data = base64.b64encode(img_data) # Odoo expects Base64
            
        # Write to Main DB (Using Odoo ENV)
        # Search by Ref (if exists) or Name
        domain = []
        if ref:
            domain = [('default_code', '=', ref)]
        else:
            domain = [('name', '=', name)] # Fallback
            
        product = env['product.template'].search(domain, limit=1)
        if product:
            product.write({'image_1920': b64_data})
            count += 1
            if count % 50 == 0:
                env.cr.commit()
                print(f"Restored {count} images...")
        else:
            # print(f"Skipping {name}: Product not found in Main DB")
            pass

    except Exception as e:
        print(f"Error restoring {name}: {e}")
        errors += 1

env.cr.commit()
cur.close()
conn.close()

print(f"DONE. Restored {count} images. Errors: {errors}")
