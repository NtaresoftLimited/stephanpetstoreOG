print("--- IMAGE CHECK START ---")
try:
    loc = env['ir.config_parameter'].sudo().get_param('ir_attachment.location')
    print(f"STORAGE PARAM: {loc}")
except:
    print("STORAGE PARAM: Error")

attachments = env['ir.attachment'].search([('res_model', '=', 'product.template'), ('mimetype', 'like', 'image/%')], limit=5)
print(f"FOUND {len(attachments)} product images.")
for a in attachments:
    print(f"ID: {a.id}, Name: {a.name}, Store Fname: {a.store_fname}, File Size: {a.file_size}")

print("--- IMAGE CHECK END ---")
