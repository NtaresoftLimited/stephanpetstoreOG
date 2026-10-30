import os

xml_path = r"D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\static\src\xml\request_stock_popup.xml"

with open(xml_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace the Destination Location block by wrapping it in a comment or replacing with empty string
to_remove = """                <!-- Destination Location -->
                <div class="mb-3 text-start">
                    <label class="form-label text-start w-100 fw-bold">Destination Location</label>
                    <input type="text" class="form-control bg-white" t-att-value="state.destinationWarehouseName" readonly="1" disabled="1" />
                    <small class="text-muted mt-1 d-block">Destination Location Auto-Detected from the point of sale warehouse</small>
                </div>"""

if to_remove in content:
    content = content.replace(to_remove, "")
    with open(xml_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print("SUCCESS: Removed Destination Location block.")
else:
    print("WARNING: Block not found exactly as expected.")
