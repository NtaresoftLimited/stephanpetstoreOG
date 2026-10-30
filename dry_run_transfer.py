import psycopg2
import os

# Connect to TEMP DB (Raw SQL)
conn = psycopg2.connect("dbname=Stephans_Temp_Restore user=odoo")
cur = conn.cursor()

# Query for attachments linked to product images
# Adjust query based on Odoo structure. 
# Attempt 1: Standard attachment link
query = """
    SELECT pt.id, pt.name, att.store_fname
    FROM product_template pt
    JOIN ir_attachment att ON att.res_model = 'product.template' 
                           AND att.res_field = 'image_1920' 
                           AND att.res_id = pt.id
    WHERE att.store_fname IS NOT NULL
    LIMIT 10;
"""

print("--- DRY RUN IMAGE FIND ---")
try:
    cur.execute(query)
    rows = cur.fetchall()
    print(f"Found {len(rows)} potential images in query.")
    
    for row in rows:
        pid, name, fname = row
        # Odoo store_fname is like "xx/xxxx..."
        # Backup extracted filestore is /tmp/restore_data/filestore/
        # Check if file exists there
        
        # NOTE: Odoo filestore structure is usually 2 chars folder.
        # e.g. store_fname = "e2/e251f..." -> /tmp/restore_data/filestore/e2/e251f...
        
        fpath = f"/tmp/restore_data/filestore/{fname}"
        exists = os.path.exists(fpath)
        print(f"Product: {name} | File: {fname} | Exists? {exists} | Size: {os.path.getsize(fpath) if exists else 'N/A'}")

except Exception as e:
    print(f"Query Error: {e}")

cur.close()
conn.close()
