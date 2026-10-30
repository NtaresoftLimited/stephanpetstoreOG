import json
import difflib

with open(r"d:\CODEX\STEPHANS OG/stephans-pet-app/scratch/sanity_products.json", "r", encoding="utf-8") as f:
    sanity_products = json.load(f)

with open(r"d:\CODEX\STEPHANS OG/stephans-pet-app/scratch/comparison_report.json", "r", encoding="utf-8") as f:
    report = json.load(f)

unmatched_excel = report['unmatched_products']

sanity_names = [p.get('name', '') for p in sanity_products]

print("=== CHECKING FUZZY MATCHES FOR 18 MISSING EXCEL PRODUCTS ===")
for u in unmatched_excel:
    name = u['name']
    close = difflib.get_close_matches(name, sanity_names, n=2, cutoff=0.7)
    if close:
        print(f"Excel: '{name}' --> Close Sanity match: {close}")
    else:
        print(f"Excel: '{name}' --> NO close match in Sanity")

# Which Sanity products were not matched to any Excel product?
with open(r"d:\CODEX\STEPHANS OG/stephans-pet-app/scratch/comparison_report.json", "r", encoding="utf-8") as f:
    rep = json.load(f)

# Find matched sanity IDs
from scripts.compare_excel_sanity import matched
matched_sanity_ids = set(m['sanity']['_id'] for m in matched)
unmatched_sanity = [p for p in sanity_products if p['_id'] not in matched_sanity_ids]

print(f"\n=== SANITY PRODUCTS NOT IN EXCEL ({len(unmatched_sanity)}) ===")
for p in unmatched_sanity:
    print(f"ID: {p['_id']} | Name: {p['name']} | Price: {p['price']} | Stock: {p['stock']}")
