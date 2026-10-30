import json

with open(r"d:\CODEX\STEPHANS OG/stephans-pet-app/scratch/comparison_report.json", "r", encoding="utf-8") as f:
    report = json.load(f)

with open(r"d:\CODEX\STEPHANS OG/stephans-pet-app/scratch/sanity_products.json", "r", encoding="utf-8") as f:
    sanity_products = json.load(f)

# Analyze no categories
no_cat = [p for p in sanity_products if not p.get('categories') or len(p['categories']) == 0]
print(f"Products without categories in Sanity: {len(no_cat)}")
for p in no_cat[:10]:
    print(f"  {p['_id']}: {p['name']}")

# Analyze price mismatches
price_mismatches = report['price_mismatches_sample']
print(f"\nPrice mismatch examples (Total: {report['price_mismatches_count']}):")
for pm in price_mismatches[:10]:
    print(f"  {pm['name']}: Excel={pm['excel_price']:,} vs Sanity={pm['sanity_price']:,}")

# Analyze stock mismatches
stock_mismatches = report['stock_mismatches_sample']
print(f"\nStock mismatch examples (Total: {report['stock_mismatches_count']}):")
for sm in stock_mismatches[:10]:
    print(f"  {sm['name']}: Excel={sm['excel_stock']} vs Sanity={sm['sanity_stock']}")
