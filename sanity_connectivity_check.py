import os
import re
import http.client
import json

# Manually parse .env from StephansEcomercewithAI directory
env_path = r"D:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\.env"
env_vars = {}
if os.path.exists(env_path):
    with open(env_path, 'r') as f:
        for line in f:
            match = re.match(r'^\s*([A-Za-z0-9_]+)\s*=\s*(.*)\s*$', line)
            if match:
                key, val = match.groups()
                env_vars[key] = val.strip()

project_id = env_vars.get('NEXT_PUBLIC_SANITY_PROJECT_ID')
dataset = env_vars.get('NEXT_PUBLIC_SANITY_DATASET')
token = env_vars.get('SANITY_API_WRITE_TOKEN')

def check_sanity():
    if not all([project_id, dataset, token]):
        print("Missing Sanity configuration in .env")
        print(f"Project ID: {'Set' if project_id else 'NOT SET'}")
        print(f"Dataset: {'Set' if dataset else 'NOT SET'}")
        print(f"Token: {'Set' if token else 'NOT SET'}")
        return

    print(f"Checking Sanity connectivity for Project: {project_id}, Dataset: {dataset}...")
    
    # Use basic HTTP request to avoid dependency issues
    conn = http.client.HTTPSConnection(f"{project_id}.api.sanity.io")
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    try:
        # Check project info
        conn.request("GET", "/v1/projects", headers=headers)
        res = conn.getresponse()
        data = res.read()
        
        if res.status == 200:
            projects = json.loads(data)
            match = next((p for p in projects if p['id'] == project_id), None)
            if match:
                print(f"Sanity connection SUCCESSFUL.")
                print(f"Project Name: {match.get('displayName', 'N/A')}")
                print(f"Organization: {match.get('organizationId', 'N/A')}")
            else:
                print(f"Authenticated, but project {project_id} not found in user's projects.")
        else:
            print(f"Sanity API Error: {res.status} {res.reason}")
            print(data.decode())

    except Exception as e:
        print(f"Error connecting to Sanity: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_sanity()
