print("--- MAPPING CHECK ---")
attachments = env['ir.attachment'].search([('res_model', '=', 'product.template'), ('mimetype', 'like', 'image/%')], limit=10)
for a in attachments:
    print(f"ID: {a.id} | Name: {a.name} | File: {a.store_fname}")
