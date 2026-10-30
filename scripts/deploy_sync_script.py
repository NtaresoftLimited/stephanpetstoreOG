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
import re
import socket
import urllib.parse
import urllib.request
import xmlrpc.client
from datetime import datetime

# Set default socket timeout
socket.setdefaulttimeout(45)

# Setup logging
LOG_FILE = "/var/log/odoo-sanity-sync.log"
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(LOG_FILE, encoding="utf-8")
    ]
)
logger = logging.getLogger("PriceSync")

LOCK_FILE = "/tmp/odoo_sanity_price_sync.lock"

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

def generate_slug(name, product_id):
    slug = name.lower()
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    slug = slug.strip('-')
    return f"{slug}-{product_id}"

def run_sync():
    # 1. Lock execution to avoid overlapping runs
    lock_fd = open(LOCK_FILE, "w")
    try:
        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        logger.info("Another sync process is already running. Exiting cleanly.")
        return

    start_time = datetime.now()
    logger.info("=== Starting Odoo -> Sanity Price Sync ===")

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

        # 3. Fetch active saleable products from Odoo
        logger.info("Fetching active products from Odoo...")
        odoo_products = models.execute_kw(
            odoo_db, uid, odoo_pass,
            "product.template", "search_read",
            [[["sale_ok", "=", True], ["active", "=", True]]],
            {"fields": ["id", "name", "list_price", "description_sale", "categ_id", "write_date"]}
        )
        logger.info(f"Retrieved {len(odoo_products)} active products from Odoo.")

        # 4. Fetch all product documents from Sanity
        logger.info("Fetching products from Sanity CMS...")
        sanity_query = '*[_type == "product"]{_id, odooId, name, price, variants}'
        query_url = f"https://{sanity_project}.api.sanity.io/v2025-12-05/data/query/{sanity_dataset}?query={urllib.parse.quote(sanity_query)}"
        req = urllib.request.Request(query_url, headers={"Authorization": f"Bearer {sanity_token}", "User-Agent": "OdooPriceSync/1.0"})
        with urllib.request.urlopen(req, timeout=45) as resp:
            sanity_docs = json.loads(resp.read().decode())["result"]
        logger.info(f"Retrieved {len(sanity_docs)} products from Sanity.")

        # Map Sanity products by odoo ID (e.g. odoo-1000 -> 1000) and by odooId
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

        # 5. Compare & generate mutations
        mutations = []
        price_updated_count = 0
        new_created_count = 0

        for op in odoo_products:
            op_id = op["id"]
            op_name = op["name"] or "Unnamed Product"
            op_price = int(round(float(op.get("list_price") or 0)))

            if op_id in sanity_by_odoo_id:
                s_doc = sanity_by_odoo_id[op_id]
                s_price = int(round(float(s_doc.get("price") or 0)))

                if s_price != op_price:
                    patch_set = {"price": op_price}
                    if s_doc.get("variants"):
                        updated_variants = []
                        for v in s_doc["variants"]:
                            v_copy = dict(v)
                            v_copy["price"] = op_price
                            updated_variants.append(v_copy)
                        patch_set["variants"] = updated_variants

                    mutations.append({
                        "patch": {
                            "id": s_doc["_id"],
                            "set": patch_set
                        }
                    })
                    price_updated_count += 1
                    logger.info(f"Price Change: [{s_doc['_id']}] {op_name}: {s_price:,} -> {op_price:,} TZS")
            else:
                # Active product in Odoo missing in Sanity: Create it safely (NO IMAGES)
                sanity_id = f"odoo-{op_id}"
                slug = generate_slug(op_name, op_id)
                mutations.append({
                    "createIfNotExists": {
                        "_type": "product",
                        "_id": sanity_id,
                        "name": op_name,
                        "price": op_price,
                        "description": op.get("description_sale") or op_name,
                        "slug": {"_type": "slug", "current": slug},
                        "odooId": op_id,
                        "odooLastModified": op.get("write_date") or "",
                        "images": []
                    }
                })
                new_created_count += 1
                logger.info(f"New Product: Created [{sanity_id}] {op_name} (Price: {op_price:,} TZS)")

        # 6. Apply mutations in batches if any
        if mutations:
            logger.info(f"Submitting {len(mutations)} mutations ({price_updated_count} price updates, {new_created_count} new products) to Sanity...")
            batch_size = 50
            for i in range(0, len(mutations), batch_size):
                batch = mutations[i:i + batch_size]
                mutate_url = f"https://{sanity_project}.api.sanity.io/v2025-12-05/data/mutate/{sanity_dataset}"
                mutate_req = urllib.request.Request(
                    mutate_url,
                    data=json.dumps({"mutations": batch}).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {sanity_token}",
                        "User-Agent": "OdooPriceSync/1.0"
                    },
                    method="POST"
                )
                with urllib.request.urlopen(mutate_req, timeout=45) as mutate_resp:
                    res = json.loads(mutate_resp.read().decode())
                    logger.info(f"Batch {i // batch_size + 1} processed successfully (Tx: {res.get('transactionId')})")
        else:
            logger.info("All prices and products are up-to-date. No changes needed.")

        duration = (datetime.now() - start_time).total_seconds()
        logger.info(f"=== Sync completed successfully in {duration:.2f}s ===\n")

    except Exception as e:
        logger.error(f"Sync error: {e}", exc_info=True)
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
with sftp.file("/opt/scripts/sync_odoo_sanity_prices.py", "w") as f:
    f.write(script_code)
sftp.close()

ssh.exec_command("chmod +x /opt/scripts/sync_odoo_sanity_prices.py")
print("Updated /opt/scripts/sync_odoo_sanity_prices.py")
ssh.close()
