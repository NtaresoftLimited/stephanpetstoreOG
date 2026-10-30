import os
import re
import xmlrpc.client
import base64
import logging
import sys
from collections import defaultdict

# Configuration
ODOO_URL = "https://erp.stephanspetstore.co.tz"
ODOO_DB = "Stephans"
ODOO_USER = "info@stephanspetstore.co.tz"
ODOO_PASSWORD = "Stephan@3202"
IMAGE_DIR = "Product Pictures"

# Setup Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def connect_odoo():
    try:
        common = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/common')
        uid = common.authenticate(ODOO_DB, ODOO_USER, ODOO_PASSWORD, {})
        if not uid:
            raise Exception("Authentication failed")
        models = xmlrpc.client.ServerProxy(f'{ODOO_URL}/xmlrpc/2/object')
        return uid, models
    except Exception as e:
        logger.error(f"Failed to connect to Odoo: {e}")
        return None, None

def normalize_name(name):
    """Normalize string for fuzzy matching."""
    # Remove file extension
    name = os.path.splitext(name)[0]
    # Remove "no X" or "n0X" suffix
    name = re.sub(r'[\s_]n[o0]\d+$', '', name, flags=re.IGNORECASE)
    name = re.sub(r'[\s_]no\s\d+$', '', name, flags=re.IGNORECASE)
    # Remove trailing numbers if they look like sequence
    name = re.sub(r'[\s_]\d+$', '', name)
    
    # Replace separators with space
    name = re.sub(r'[-_]', ' ', name)
    # Remove extra spaces
    name = re.sub(r'\s+', ' ', name).strip().lower()
    return name

def get_image_files():
    if not os.path.exists(IMAGE_DIR):
        logger.error(f"Directory {IMAGE_DIR} not found.")
        return {}
    
    files = [f for f in os.listdir(IMAGE_DIR) if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
    grouped = defaultdict(list)
    
    for f in files:
        # Extract sequence if possible for sorting
        seq_match = re.search(r'[nN][o0]\s?(\d+)', f)
        seq = int(seq_match.group(1)) if seq_match else 999
        
        # Determine product name key
        # Heuristic: Remove the "no X" part
        clean_name = re.sub(r'[\s_]?[nN][o0]\s?\d+.*$', '', os.path.splitext(f)[0])
        clean_name = re.sub(r'[-_]', ' ', clean_name).strip().lower()
        
        grouped[clean_name].append({'file': f, 'seq': seq})
        
    for k in grouped:
        grouped[k].sort(key=lambda x: x['seq'])
        
    return grouped

def match_score(local_name, odoo_name):
    # Tokenize
    set1 = set(normalize_name(local_name).split())
    set2 = set(normalize_name(odoo_name).split())
    
    if not set1 or not set2:
        return 0.0
    
    intersection = set1.intersection(set2)
    score = len(intersection) / max(len(set1), len(set2)) # Jaccard Index
    return score

def main():
    logger.info("Starting Product Image Update...")
    
    uid, models = connect_odoo()
    if not uid:
        sys.exit(1)
        
    # Fetch Odoo Products
    logger.info("Fetching products from Odoo...")
    products = models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD,
        'product.template', 'search_read',
        [[]],
        {'fields': ['id', 'name', 'default_code']})
    
    local_images = get_image_files()
    logger.info(f"Found {len(local_images)} local product image groups.")
    
    success_count = 0
    fail_count = 0
    
    for local_name, images in local_images.items():
        best_match = None
        best_score = 0.0
        
        # Try finding best match
        for p in products:
            # 1. Exact Name
            if normalize_name(p['name']) == normalize_name(local_name):
                best_match = p
                best_score = 1.0
                break
                
            # 2. Exact Code
            if p.get('default_code') and normalize_name(p['default_code']) == normalize_name(local_name):
                best_match = p
                best_score = 1.0
                break
            
            # 3. Fuzzy Score
            score = match_score(local_name, p['name'])
            if score > best_score:
                best_score = score
                best_match = p
        
        if best_score < 0.7: # Threshold
             logger.warning(f"No match found for local group: '{local_name}' (Best score: {best_score})")
             fail_count += 1
             continue
            
        product = best_match
        logger.info(f"Matched '{local_name}' to Odoo Product '{product['name']}' (ID: {product['id']}, Score: {best_score:.2f})")
        
        try:
            # Process images
            # First image -> Main Image (image_1920)
            main_img_file = images[0]['file']
            with open(os.path.join(IMAGE_DIR, main_img_file), "rb") as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')
            
            # Update Main Image
            models.execute_kw(ODOO_DB, uid, ODOO_PASSWORD, 'product.template', 'write', [[product['id']], {'image_1920': img_data}])
            logger.info(f"  - Updated main image from {main_img_file}")
            
            # Skip product.image for now as model is missing
            if len(images) > 1:
                logger.info(f"  - Found {len(images)-1} extra images. Skipping Odoo upload (model missing). Ensure Sanity sync picks them up.")
                
            success_count += 1
            
        except Exception as e:
            logger.error(f"  - Error updating product {product['name']}: {e}")
            fail_count += 1

    logger.info(f"Done. Success: {success_count}, Failed: {fail_count}")

if __name__ == "__main__":
    main()
