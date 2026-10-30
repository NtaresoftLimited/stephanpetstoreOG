import paramiko

token = None
with open(r"d:\CODEX\STEPHANS OG\stephans-pet-app\StephansEcomercewithAI\.env") as f:
    for line in f:
        if line.startswith("SANITY_API_WRITE_TOKEN="):
            token = line.split("=", 1)[1].strip().strip('"').strip("'")
            break

print("Token extracted successfully. Length:", len(token))

# Connect to server and write /etc/odoo-sanity-sync.env
HOST = "166.1.227.63"
USER = "root"
PASSWORD = "wpo,,CWc2VH^PZ"

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

env_content = f"""# Odoo & Sanity Sync Configuration
ODOO_URL=http://127.0.0.1:8071
ODOO_DB=Stephans
ODOO_USER=info@stephanspetstore.co.tz
ODOO_PASSWORD=Stephan@3202

SANITY_PROJECT_ID=ubqcgegx
SANITY_DATASET=production
SANITY_API_WRITE_TOKEN={token}
"""

sftp = ssh.open_sftp()
with sftp.file("/etc/odoo-sanity-sync.env", "w") as f:
    f.write(env_content)
sftp.close()

# Secure env file permissions
ssh.exec_command("chmod 600 /etc/odoo-sanity-sync.env")
print("/etc/odoo-sanity-sync.env created with chmod 600!")
ssh.close()
