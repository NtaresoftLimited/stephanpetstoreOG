import os

xml_path = r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\static\src\xml\replenishment_request_popup.xml"

with open(xml_path, 'r', encoding='utf-8') as f:
    content = f.read()

to_remove = """                <div class="mb-3 mt-4">
                    <label class="form-label text-start w-100 fw-bold">Store Location (Destination)</label>
                    <input type="text" class="form-control" t-att-value="state.destinationWarehouseName" readonly="1" disabled="1" />
                </div>"""

if to_remove in content:
    content = content.replace(to_remove, "")
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Removed Store Location block.")
else:
    print("WARNING: Block not found exactly as expected. Let me try with different whitespace.")
    
    # fallback
    import re
    new_content = re.sub(r'<div class="mb-3 mt-4">\s*<label class="form-label text-start w-100 fw-bold">Store Location \(Destination\)</label>\s*<input type="text" class="form-control" t-att-value="state.destinationWarehouseName" readonly="1" disabled="1" />\s*</div>', '', content)
    if new_content != content:
        with open(xml_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print("SUCCESS: Removed with regex.")
    else:
        print("Still failed to remove.")
