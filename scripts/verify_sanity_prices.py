import urllib.request
import urllib.parse
import json

test_ids = ["odoo-2596", "odoo-2735", "odoo-1606", "odoo-1079", "odoo-944", "odoo-3017"]
groq = f'*[_type == "product" && _id in {json.dumps(test_ids)}]{{_id, name, price, variants}}'
url = f"https://ubqcgegx.api.sanity.io/v2025-12-05/data/query/production?query={urllib.parse.quote(groq)}"

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode())['result']

for r in res:
    v_prices = [v.get('price') for v in (r.get('variants') or [])]
    print(f"[{r['_id']}] {r['name']} => Price: {r['price']:,} TZS | Variants: {v_prices}")
