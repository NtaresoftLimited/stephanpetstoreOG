import json

with open(r"d:\CODEX\STEPHANS OG/stephans-pet-app/scratch/sanity_products.json", "r", encoding="utf-8") as f:
    sanity_products = json.load(f)

no_img = [p for p in sanity_products if not p.get('hasImages') or p.get('imagesCount', 0) == 0]
print(f"Total products without images in Sanity: {len(no_img)}")
for p in no_img:
    print(f"  ID: {p['_id']} | Name: {p['name']} | Price: {p['price']} | Stock: {p['stock']}")
