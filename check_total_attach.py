print("--- TOTAL ATTACHMENTS ---")
count = env['ir.attachment'].search_count([])
print(f"Total Attachments: {count}")

print("--- SAMPLE ATTACHMENTS ---")
attachments = env['ir.attachment'].search([], limit=5)
for a in attachments:
    print(f"Model: {a.res_model} | ID: {a.res_id} | File: {a.store_fname}")
