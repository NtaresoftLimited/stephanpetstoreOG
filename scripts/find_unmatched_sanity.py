import json

with open(r"d:\CODEX\STEPHANS OG/stephans-pet-app/scratch/sanity_products.json", "r", encoding="utf-8") as f:
    sanity_products = json.load(f)

# Re-run matching cleanly
import openpyxl
import re

wb = openpyxl.load_workbook(r"C:\Users\fisto\Downloads\Stephans pet store, Both Sotore Product (product.template).xlsx", data_only=True)
sheet = wb.active
headers = [sheet.cell(row=1, column=c).value for c in range(1, sheet.max_column + 1)]

excel_products = []
for r in range(2, sheet.max_row + 1):
    name = sheet.cell(row=r, column=headers.index('Name') + 1).value
    if name:
        sku = sheet.cell(row=r, column=headers.index('Internal Reference') + 1).value
        excel_products.append({
            'name': name.strip(),
            'sku': str(sku).strip() if sku else None
        })

def norm(s):
    return re.sub(r'[\s\-_/]+', ' ', s.lower().strip()) if s else ""

matched_sanity_ids = set()
for ep in excel_products:
    for sp in sanity_products:
        sp_name = sp.get('name', '').strip()
        if ep['name'] == sp_name or norm(ep['name']) == norm(sp_name):
            matched_sanity_ids.add(sp['_id'])
            break

unmatched_sanity = [p for p in sanity_products if p['_id'] not in matched_sanity_ids]
print(f"Total Sanity products: {len(sanity_products)}")
print(f"Matched Sanity products: {len(matched_sanity_ids)}")
print(f"Unmatched in Sanity: {len(unmatched_sanity)}")
for p in unmatched_sanity:
    print(f"  ID: {p['_id']} | Name: {p['name']} | Price: {p['price']} | Stock: {p['stock']} | HasImages: {p.get('hasImages')}")
