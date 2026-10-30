import urllib.request
import urllib.parse
import json
import xmlrpc.client

# 1. Fetch Sanity products without images
groq = '*[_type == "product" && (!defined(images) || count(images) == 0)]{_id, odooId, name}'
url = f"https://ubqcgegx.api.sanity.io/v2025-12-05/data/query/production?query={urllib.parse.quote(groq)}"

req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
with urllib.request.urlopen(req) as resp:
    sanity_no_img = json.loads(resp.read().decode())['result']

print(f"Products in Sanity WITHOUT images: {len(sanity_no_img)}")
for p in sanity_no_img:
    print(f"  [{p['_id']}] {p['name']}")
