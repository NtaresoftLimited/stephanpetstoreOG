import urllib.request
import json
import os

token = None
with open(r"d:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\.env", "r") as f:
    for line in f:
        if line.startswith("SANITY_API_WRITE_TOKEN="):
            token = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

print("Token found:", bool(token), "Length:", len(token) if token else 0)

# Test query with auth
url = "https://ubqcgegx.api.sanity.io/v2025-12-05/data/mutate/production?dryRun=true"

# Let's test dryRun mutation on 1 document
mutations = {
    "mutations": [
        {
            "patch": {
                "id": "odoo-2596",
                "set": {
                    "price": 75000
                }
            }
        }
    ]
}

req = urllib.request.Request(
    url,
    data=json.dumps(mutations).encode('utf-8'),
    headers={
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}'
    },
    method='POST'
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        print("Dry run mutation SUCCESS:", res)
except Exception as e:
    print("Dry run mutation FAILED:", e)
