import urllib.request
import urllib.parse
import json

groq = '*[_type == "product"]{_id, odooId, name, price, stock, "variants": variants[]{sku, name, price, stock}, "hasImages": count(images) > 0, "imagesCount": count(images), "slug": slug.current, "categories": categories[]->title}'

url = f"https://ubqcgegx.api.sanity.io/v2025-12-05/data/query/production?query={urllib.parse.quote(groq)}"

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode())['result']

print(f"Fetched {len(data)} products from Sanity.")

with open(r"d:\CODEX\STEPHANS OG\stephans-pet-app\scratch\sanity_products.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("Saved to scratch/sanity_products.json")
