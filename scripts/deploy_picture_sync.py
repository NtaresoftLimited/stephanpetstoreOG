import paramiko

HOST = "166.1.227.63"
USER = "root"
PASSWORD = "wpo,,CWc2VH^PZ"

script_code = r'''#!/usr/bin/env python3
import os
import sys
import fcntl
import json
import logging
import hashlib
import base64
import socket
import urllib.parse
import urllib.request
import xmlrpc.client
from datetime import datetime
import uuid

# Set default socket timeout
socket.setdefaulttimeout(60)

# Setup logging
LOG_FILE = "/var/log/odoo-sanity-picture-sync.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)
logger = logging.getLogger("PictureSync")

LOCK_FILE = "/tmp/odoo_sanity_picture_sync.lock"

def load_env(env_path="/etc/odoo-sanity-sync.env"):
    config = {}
    if not os.path.exists(env_path):
        raise FileNotFoundError(f"Configuration file {env_path} not found.")
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                config[k.strip()] = v.strip().strip('"').strip("'")
    return config

def upload_image_to_sanity(img_bytes, filename, project_id, dataset, token):
    content_type = "image/jpeg"
    if img_bytes.startswith(b"\x89PNG"):
        content_type = "image/png"
    elif img_bytes.startswith(b"GIF"):
        content_type = "image/gif"
    elif img_bytes.startswith(b"RIFF") and img_bytes[8:12] == b"WEBP":
        content_type = "image/webp"

    url = f"https://{project_id}.api.sanity.io/v2025-12-05/assets/images/{dataset}?filename={urllib.parse.quote(filename)}"
    req = urllib.request.Request(
        url,
        data=img_bytes,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": content_type,
            "User-Agent": "OdooPictureSync/1.0"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        res = json.loads(resp.read().decode())
        return res.get("document", {}).get("_id")

def run_sync():
    # 1. Lock execution to avoid overlapping runs
    lock_fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        logger.info("Another picture sync process is already running. Exiting cleanly.")
        return

    start_time = datetime.now()
    logger.info("=== Starting Odoo -> Sanity Picture Sync ===")

    try:
        cfg = load_env()
        odoo_url = cfg.get("ODOO_URL", "http://127.0.0.1:8071")
        odoo_db = cfg.get("ODOO_DB", "Stephans")
        odoo_user = cfg.get("ODOO_USER", "info@stephanspetstore.co.tz")
        odoo_pass = cfg.get("ODOO_PASSWORD", "Stephan@3202")

        sanity_project = cfg.get("SANITY_PROJECT_ID", "ubqcgegx")
        sanity_dataset = cfg.get("SANITY_DATASET", "production")
        sanity_token = cfg.get("SANITY_API_WRITE_TOKEN")

        if not sanity_token:
            raise ValueError("SANITY_API_WRITE_TOKEN is missing in config.")

        # 2. Connect to Odoo via XML-RPC
        common = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/common")
        uid = common.authenticate(odoo_db, odoo_user, odoo_pass, {})
        if not uid:
            raise ConnectionError(f"Odoo authentication failed for user {odoo_user}")

        models = xmlrpc.client.ServerProxy(f"{odoo_url}/xmlrpc/2/object")

        # 3. Lightweight fetch: active products from Odoo (id, name, write_date)
        logger.info("Scanning active products from Odoo...")
        odoo_products = models.execute_kw(
            odoo_db, uid, odoo_pass,
            "product.template", "search_read",
            [[["sale_ok", "=", True], ["active", "=", True]]],
            {"fields": ["id", "name", "write_date"]}
        )
        logger.info(f"Retrieved {len(odoo_products)} active products from Odoo.")
        odoo_by_id = {op["id"]: op for op in odoo_products}

        # 4. Fetch Sanity products image status
        logger.info("Fetching picture status from Sanity CMS...")
        sanity_query = '*[_type == "product"]{_id, odooId, odooLastModified, odooImageHash, "hasImages": count(images) > 0}'
        query_url = f"https://{sanity_project}.api.sanity.io/v2025-12-05/data/query/{sanity_dataset}?query={urllib.parse.quote(sanity_query)}"
        req = urllib.request.Request(query_url, headers={"Authorization": f"Bearer {sanity_token}", "User-Agent": "OdooPictureSync/1.0"})
        with urllib.request.urlopen(req, timeout=45) as resp:
            sanity_docs = json.loads(resp.read().decode())["result"]
        logger.info(f"Retrieved {len(sanity_docs)} products from Sanity.")

        # Map Sanity products by odoo ID
        sanity_by_odoo_id = {}
        for doc in sanity_docs:
            doc_id = doc.get("_id", "")
            if doc_id.startswith("odoo-"):
                try:
                    num_id = int(doc_id.replace("odoo-", ""))
                    sanity_by_odoo_id[num_id] = doc
                except ValueError:
                    pass
            elif doc.get("odooId"):
                sanity_by_odoo_id[doc["odooId"]] = doc

        # 5. Identify candidates that need image checking:
        # - Products in Sanity that currently have NO images (hasImages == False)
        # - Products whose write_date changed since last modified
        candidates = []
        for op in odoo_products:
            op_id = op["id"]
            if op_id in sanity_by_odoo_id:
                s_doc = sanity_by_odoo_id[op_id]
                has_images = s_doc.get("hasImages", False)
                odoo_write = op.get("write_date")
                last_modified = s_doc.get("odooLastModified")

                if not has_images or (odoo_write and odoo_write != last_modified):
                    candidates.append((op, s_doc))

        logger.info(f"Identified {len(candidates)} candidate products to check for new/updated pictures.")

        uploaded_count = 0
        skipped_count = 0

        # Process candidates in batches to read image_1920
        batch_size = 20
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]
            candidate_ids = [op["id"] for op, s_doc in batch]

            images_data = models.execute_kw(
                odoo_db, uid, odoo_pass,
                "product.template", "read",
                [candidate_ids],
                {"fields": ["id", "image_1920"]}
            )
            images_by_id = {r["id"]: r.get("image_1920") for r in images_data}

            for op, s_doc in batch:
                op_id = op["id"]
                op_name = op["name"]
                img_b64 = images_by_id.get(op_id)

                if not img_b64 or len(img_b64) < 200:
                    skipped_count += 1
                    continue

                # Compute MD5 of the base64 image
                img_hash = hashlib.md5(img_b64.encode("utf-8")).hexdigest()
                current_hash = s_doc.get("odooImageHash")

                # If the image hash is unchanged, no re-upload needed
                if current_hash == img_hash and s_doc.get("hasImages"):
                    skipped_count += 1
                    continue

                try:
                    logger.info(f"Uploading picture for [{s_doc['_id']}] {op_name} (Hash: {img_hash[:8]})...")
                    img_bytes = base64.b64decode(img_b64)
                    filename = f"odoo_{op_id}.jpg"
                    asset_id = upload_image_to_sanity(img_bytes, filename, sanity_project, sanity_dataset, sanity_token)

                    if asset_id:
                        # Patch product in Sanity with new image and hash
                        patch_url = f"https://{sanity_project}.api.sanity.io/v2025-12-05/data/mutate/{sanity_dataset}"
                        image_key = f"odoo-img-{uuid.uuid4().hex[:8]}"
                        patch_payload = {
                            "mutations": [
                                {
                                    "patch": {
                                        "id": s_doc["_id"],
                                        "set": {
                                            "images": [
                                                {
                                                    "_type": "image",
                                                    "_key": image_key,
                                                    "asset": {
                                                        "_type": "reference",
                                                        "_ref": asset_id
                                                    }
                                                }
                                            ],
                                            "odooImageHash": img_hash,
                                            "odooLastModified": op.get("write_date") or ""
                                        }
                                    }
                                }
                            ]
                        }
                        patch_req = urllib.request.Request(
                            patch_url,
                            data=json.dumps(patch_payload).encode("utf-8"),
                            headers={
                                "Content-Type": "application/json",
                                "Authorization": f"Bearer {sanity_token}",
                                "User-Agent": "OdooPictureSync/1.0"
                            },
                            method="POST"
                        )
                        with urllib.request.urlopen(patch_req, timeout=45) as patch_resp:
                            uploaded_count += 1
                            logger.info(f"SUCCESS: Picture updated for [{s_doc['_id']}] {op_name} (Asset: {asset_id})")
                except Exception as err:
                    logger.error(f"Failed to upload picture for {op_name} (ID {op_id}): {err}")

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"=== Picture sync completed in {duration:.2f}s: {uploaded_count} pictures uploaded, {skipped_count} skipped. ===\n")

    except Exception as e:
        logger.error(f"Picture sync error: {e}", exc_info=True)
    finally:
        fcntl.flock(lock_fd, fcntl.LOCK_UN)
        lock_fd.close()

if __name__ == "__main__":
    run_sync()
'''

ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect(HOST, username=USER, password=PASSWORD)

sftp = ssh.open_sftp()
with sftp.file("/opt/scripts/sync_odoo_sanity_pictures.py", "w") as f:
    f.write(script_code)
sftp.close()

ssh.exec_command("chmod +x /opt/scripts/sync_odoo_sanity_pictures.py")
print("Uploaded /opt/scripts/sync_odoo_sanity_pictures.py with chmod +x")
ssh.close()
