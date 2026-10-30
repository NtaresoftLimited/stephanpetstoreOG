import urllib.request
import json
import base64

token = None
with open(r"d:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\.env") as f:
    for line in f:
        if line.startswith("SANITY_API_WRITE_TOKEN="):
            token = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

# 1x1 transparent PNG bytes
png_b64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
img_bytes = base64.b64decode(png_b64)

url = "https://ubqcgegx.api.sanity.io/v2025-12-05/assets/images/production?filename=test_pixel.png"

req = urllib.request.Request(
    url,
    data=img_bytes,
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "image/png"
    },
    method="POST"
)

try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        print("Upload SUCCESS! Asset doc:", res.get("document", {}).get("_id"))
        # Clean up test asset
        asset_id = res.get("document", {}).get("_id")
        if asset_id:
            del_url = f"https://ubqcgegx.api.sanity.io/v2025-12-05/data/mutate/production"
            del_req = urllib.request.Request(
                del_url,
                data=json.dumps({"mutations": [{"delete": {"id": asset_id}}]}).encode(),
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                method="POST"
            )
            with urllib.request.urlopen(del_req) as del_resp:
                print("Deleted test asset:", asset_id)
except Exception as e:
    print("Upload FAILED:", e)
