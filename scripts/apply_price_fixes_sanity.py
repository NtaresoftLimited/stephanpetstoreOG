import json
import urllib.request
import urllib.parse

# 1. Load token
token = None
with open(r"d:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\.env", "r") as f:
    for line in f:
        if line.startswith("SANITY_API_WRITE_TOKEN="):
            token = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

if not token:
    raise ValueError("SANITY_API_WRITE_TOKEN not found!")

# 2. Load verified price diffs
with open(r"d:\CODEX\STEPHANS OG\stephans-pet-app\scratch\verified_price_diffs.json", "r", encoding="utf-8") as f:
    price_diffs = json.load(f)

# Add the 2 additional verified products:
# - True Touch Deshedding Brush L: 20,000 -> 35,000
# - Stainless Steel Muzzle L: 45,000 -> 73,000
additional = [
    {
        'id': 'odoo-1079',
        'name': 'True Touch Deshedding Brush L',
        'excel_name': 'True Touch DE shedding Brush',
        'sanity_price': 20000.0,
        'new_price': 35000.0
    },
    {
        'id': 'odoo-944',
        'name': 'Stainless Steel Muzzle L',
        'excel_name': 'Stainless Steel Muzzle Old',
        'sanity_price': 45000.0,
        'new_price': 73000.0
    }
]

# Ensure no duplicates
existing_ids = set(p['id'] for p in price_diffs)
for add in additional:
    if add['id'] not in existing_ids:
        price_diffs.append(add)

print(f"Total products to update in Sanity: {len(price_diffs)}")

# Query current variants for all these products so we update both main price and variant prices
ids_list = [p['id'] for p in price_diffs]
groq = f'*[_type == "product" && _id in {json.dumps(ids_list)}]{{_id, name, price, variants}}'
query_url = f"https://ubqcgegx.api.sanity.io/v2025-12-05/data/query/production?query={urllib.parse.quote(groq)}"

req = urllib.request.Request(query_url, headers={'Authorization': f'Bearer {token}'})
with urllib.request.urlopen(req) as resp:
    sanity_docs = json.loads(resp.read().decode())['result']

docs_by_id = {d['_id']: d for d in sanity_docs}

mutations = []
for pd in price_diffs:
    doc_id = pd['id']
    new_price = int(pd['new_price'])
    patch_set = {
        'price': new_price
    }
    
    # If variants exist, update variants too
    doc = docs_by_id.get(doc_id)
    if doc and doc.get('variants'):
        updated_variants = []
        for v in doc['variants']:
            v_copy = dict(v)
            v_copy['price'] = new_price
            updated_variants.append(v_copy)
        patch_set['variants'] = updated_variants
        
    mutations.append({
        'patch': {
            'id': doc_id,
            'set': patch_set
        }
    })

print(f"Constructed {len(mutations)} patch mutations.")

# Submit mutations to Sanity
mutate_url = "https://ubqcgegx.api.sanity.io/v2025-12-05/data/mutate/production"

mutate_req = urllib.request.Request(
    mutate_url,
    data=json.dumps({'mutations': mutations}).encode('utf-8'),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    },
    method='POST'
)

with urllib.request.urlopen(mutate_req) as resp:
    result = json.loads(resp.read().decode())
    print("Sanity Mutation Result:", result)

print("SUCCESS: All 53 product prices have been applied to Sanity!")
