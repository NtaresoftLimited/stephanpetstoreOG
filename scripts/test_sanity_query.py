import urllib.request
import urllib.parse
import json

def sanity_query(groq):
    url = f"https://ubqcgegx.api.sanity.io/v2025-12-05/data/query/production?query={urllib.parse.quote(groq)}"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())['result']

print("Total products in Sanity:", sanity_query('count(*[_type == "product"])'))
print("Total odoo products in Sanity:", sanity_query('count(*[_type == "product" && _id in path("odoo-*")])'))
print("Draft products in Sanity:", sanity_query('count(*[_id in path("drafts.**") && _type == "product"])'))

# Sample document keys
sample = sanity_query('*[_type == "product"][0]')
print("Fields in sample product:", list(sample.keys()))
print("Sample product:", json.dumps(sample, indent=2))
