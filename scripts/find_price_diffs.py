import json
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
        price = sheet.cell(row=r, column=headers.index('Sales Price') + 1).value or 0
        excel_products.append({
            'row': r,
            'name': name.strip(),
            'sku': str(sku).strip() if sku else None,
            'price': float(price)
        })

with open(r"d:\CODEX\STEPHANS OG\stephans-pet-app\scratch\sanity_products.json", "r", encoding="utf-8") as f:
    sanity_products = json.load(f)

def norm(s):
    return re.sub(r'[\s\-_/]+', ' ', s.lower().strip()) if s else ""

sanity_by_name = {p.get('name', '').strip(): p for p in sanity_products}
sanity_by_norm = {norm(p.get('name', '')): p for p in sanity_products}

# Known slight name differences
extra_mappings = {
    'Round Ear Shaped Cat Bed': 'Round Ear Shape Cat Bed',
    'WaterProof Squire Dog Bed': 'WaterProof Squire Dog Bed L',
    'Thick Soft Pet Blanket M': 'Thick Soft Blanket M',
}

price_diffs = []
seen_ids = set()

for ep in excel_products:
    sp = None
    if ep['name'] in sanity_by_name:
        sp = sanity_by_name[ep['name']]
    elif norm(ep['name']) in sanity_by_norm:
        sp = sanity_by_norm[norm(ep['name'])]
    elif ep['name'] in extra_mappings:
        target_name = extra_mappings[ep['name']]
        sp = sanity_by_name.get(target_name)

    if sp and sp['_id'] not in seen_ids:
        sp_price = float(sp.get('price') or 0)
        ep_price = float(ep['price'])
        if sp_price != ep_price:
            seen_ids.add(sp['_id'])
            price_diffs.append({
                'id': sp['_id'],
                'name': sp['name'],
                'excel_name': ep['name'],
                'sanity_price': sp_price,
                'new_price': ep_price,
            })

print(f"Total verified products with price differences: {len(price_diffs)}")
for i, pd in enumerate(price_diffs, 1):
    print(f"{i:2d}. [{pd['id']}] {pd['name']}: {pd['sanity_price']:,} -> {pd['new_price']:,} TZS")

with open(r"d:\CODEX\STEPHANS OG\stephans-pet-app\scratch\verified_price_diffs.json", "w", encoding="utf-8") as f:
    json.dump(price_diffs, f, indent=2, ensure_ascii=False)
