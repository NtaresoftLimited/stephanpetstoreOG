import json
import openpyxl
import re

# 1. Load Excel products
wb = openpyxl.load_workbook(r"C:\Users\fisto\Downloads\Stephans pet store, Both Sotore Product (product.template).xlsx", data_only=True)
sheet = wb.active
headers = [sheet.cell(row=1, column=c).value for c in range(1, sheet.max_column + 1)]

excel_products = []
current_prod = None

for r in range(2, sheet.max_row + 1):
    name = sheet.cell(row=r, column=headers.index('Name') + 1).value
    if name:
        current_prod = {
            'row': r,
            'name': name.strip(),
            'sku': sheet.cell(row=r, column=headers.index('Internal Reference') + 1).value,
            'price': sheet.cell(row=r, column=headers.index('Sales Price') + 1).value or 0,
            'cost': sheet.cell(row=r, column=headers.index('Cost') + 1).value or 0,
            'pos_category': [sheet.cell(row=r, column=headers.index('Point of Sale Category') + 1).value],
            'available_in_pos': sheet.cell(row=r, column=headers.index('Available in POS') + 1).value,
            'product_category': sheet.cell(row=r, column=headers.index('Product Category') + 1).value,
            'product_type': sheet.cell(row=r, column=headers.index('Product Type') + 1).value,
            'stock': sheet.cell(row=r, column=headers.index('Quantity On Hand') + 1).value or 0,
            'active': sheet.cell(row=r, column=headers.index('Active') + 1).value,
            'approval_status': sheet.cell(row=r, column=headers.index('Approval Status') + 1).value,
        }
        if current_prod['sku']:
            current_prod['sku'] = str(current_prod['sku']).strip()
        excel_products.append(current_prod)
    else:
        pos_cat = sheet.cell(row=r, column=headers.index('Point of Sale Category') + 1).value
        if pos_cat and current_prod:
            current_prod['pos_category'].append(pos_cat)

# 2. Load Sanity products
with open(r"d:\CODEX\STEPHANS OG\stephans-pet-app\scratch\sanity_products.json", "r", encoding="utf-8") as f:
    sanity_products = json.load(f)

print(f"Excel products count: {len(excel_products)}")
print(f"Sanity products count: {len(sanity_products)}")

def normalize(s):
    if not s:
        return ""
    # remove special chars, lowercase, collapse spaces
    s = s.lower().strip()
    s = re.sub(r'[\s\-_/]+', ' ', s)
    return s

# Index Sanity products
sanity_by_name = {}
sanity_by_norm_name = {}
sanity_by_sku = {}

for p in sanity_products:
    p_name = p.get('name', '').strip()
    sanity_by_name[p_name] = p
    sanity_by_norm_name[normalize(p_name)] = p
    
    # variants
    for v in (p.get('variants') or []):
        sku = v.get('sku')
        if sku:
            sanity_by_sku[sku.strip().upper()] = p

# Matching
matched = []
unmatched = []

for ep in excel_products:
    match = None
    match_type = None
    
    # 1. Exact name
    if ep['name'] in sanity_by_name:
        match = sanity_by_name[ep['name']]
        match_type = 'exact_name'
    # 2. Normalized name
    elif normalize(ep['name']) in sanity_by_norm_name:
        match = sanity_by_norm_name[normalize(ep['name'])]
        match_type = 'norm_name'
    # 3. By SKU
    elif ep['sku'] and ep['sku'].upper() in sanity_by_sku:
        match = sanity_by_sku[ep['sku'].upper()]
        match_type = 'sku'
    
    if match:
        matched.append({
            'excel': ep,
            'sanity': match,
            'match_type': match_type
        })
    else:
        unmatched.append(ep)

print(f"\n--- MATCHING RESULTS ---")
print(f"Matched: {len(matched)} / {len(excel_products)} ({len(matched)/len(excel_products)*100:.1f}%)")
print(f"Unmatched (Missing from Sanity): {len(unmatched)}")

# Analyze unmatched products
print(f"\n--- MISSING FROM SANITY (Sample of {len(unmatched)}) ---")
for u in unmatched[:20]:
    print(f"Row {u['row']}: {u['name']} | SKU: {u['sku']} | Price: {u['price']} | Stock: {u['stock']} | Cat: {u['product_category']}")

# Analyze quality of matched products
no_images = []
price_mismatch = []
stock_mismatch = []
no_categories = []
no_slug = []

for m in matched:
    ep = m['excel']
    sp = m['sanity']
    
    # Images
    if not sp.get('hasImages') or sp.get('imagesCount', 0) == 0:
        no_images.append(m)
        
    # Price
    if float(ep['price']) != float(sp.get('price') or 0):
        price_mismatch.append({
            'name': ep['name'],
            'excel_price': ep['price'],
            'sanity_price': sp.get('price')
        })
        
    # Stock
    if int(round(float(ep['stock']))) != int(round(float(sp.get('stock') or 0))):
        stock_mismatch.append({
            'name': ep['name'],
            'excel_stock': ep['stock'],
            'sanity_stock': sp.get('stock')
        })
        
    # Categories
    if not sp.get('categories') or len(sp['categories']) == 0:
        no_categories.append(m)
        
    # Slug
    if not sp.get('slug'):
        no_slug.append(m)

print(f"\n--- QUALITY METRICS OF MATCHED PRODUCTS ({len(matched)}) ---")
print(f"Products WITH images: {len(matched) - len(no_images)} ({((len(matched)-len(no_images))/len(matched))*100:.1f}%)")
print(f"Products WITHOUT images: {len(no_images)}")
print(f"Price Mismatches: {len(price_mismatch)}")
print(f"Stock Mismatches: {len(stock_mismatch)}")
print(f"Products WITHOUT categories: {len(no_categories)}")
print(f"Products WITHOUT slug: {len(no_slug)}")

# Save detailed report to json
report = {
    'total_excel_products': len(excel_products),
    'total_sanity_products': len(sanity_products),
    'matched_count': len(matched),
    'unmatched_count': len(unmatched),
    'unmatched_products': unmatched,
    'missing_images_count': len(no_images),
    'missing_images_sample': [m['excel']['name'] for m in no_images[:20]],
    'price_mismatches_count': len(price_mismatch),
    'price_mismatches_sample': price_mismatch[:20],
    'stock_mismatches_count': len(stock_mismatch),
    'stock_mismatches_sample': stock_mismatch[:20],
}

with open(r"d:\CODEX\STEPHANS OG\stephans-pet-app\scratch\comparison_report.json", "w", encoding="utf-8") as f:
    json.dump(report, f, ensure_ascii=False, indent=2)

print("\nSaved detailed report to scratch/comparison_report.json")
