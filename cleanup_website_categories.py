import argparse
import json
import xmlrpc.client


URL = "https://erp.stephanspetstore.co.tz"
DB = "Stephans"
USERNAME = "info@stephanspetstore.co.tz"
PASSWORD = "Stephan@3202"

# Stray one-off categories are migrated into the canonical shop hierarchy.
PLACEHOLDER_CATEGORY_MAP = {
    1306: 1183,  # cat scratcher -> Cat scratching pads & boards
    1307: 1155,  # bow -> Cat decorative accessories
    1308: 1221,  # product-name rug category -> Dog rugs
    1309: 1236,  # coll -> Dog collars
    1310: 1292,  # loose Small Animals / Feeders path
    1311: 1293,  # loose Small Animals water bowls path
    1312: 1293,
    1313: 1292,  # loose Small Animals water bottle path
    1314: 1292,
    1315: 1295,  # loose Small Animals cage-clean path
    1316: 1299,  # duplicate loose house paths
    1317: 1299,
    1318: 1302,  # duplicate loose toy paths
    1319: 1302,
    1320: 1273,  # loose supplement path
}

# A few active products were left in the generic All/legacy tree. These are
# deterministic corrections based on their product names and canonical leaves.
PRODUCT_CATEGORY_FIXES = {
    740: 1151,   # Balls Cat Collar
    1217: 1230,  # Green Toy Shuanghong
    1254: 1128,  # Water Fountain Filter
    1356: 1103,  # Nanovit Granulat bird feed/supplement
    2821: 1212,  # Flower Shaped Slow Feeder Bowl
    2981: 1302,  # Hamster Hidden Toy
    2997: 1183,  # Scratching Board
    3013: 1231,  # Dog Life Fetchstix L
    3014: 1234,  # Vinyl Toy
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    common = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/common", allow_none=True)
    uid = common.authenticate(DB, USERNAME, PASSWORD, {})
    if not uid:
        raise SystemExit("Authentication failed")
    models = xmlrpc.client.ServerProxy(f"{URL}/xmlrpc/2/object", allow_none=True)

    def call(model, method, positional=None, keyword=None):
        return models.execute_kw(DB, uid, PASSWORD, model, method, positional or [], keyword or {})

    all_products = call(
        "product.template", "search_read", [[]],
        {"fields": ["name", "active", "sale_ok", "categ_id", "x_website_category_ids"],
         "context": {"active_test": False}, "order": "id"},
    )
    active_shop = [p for p in all_products if p["active"] and p["sale_ok"]]
    before = {
        "active_shop_products": len(active_shop),
        "missing": sum(not p["x_website_category_ids"] for p in active_shop),
        "multiple": sum(len(p["x_website_category_ids"]) > 1 for p in active_shop),
        "mismatch": sum(
            bool(p["x_website_category_ids"])
            and p["categ_id"][0] not in p["x_website_category_ids"]
            for p in active_shop
        ),
    }

    proposed = []
    for product in all_products:
        current_category = product["categ_id"][0]
        final_category = PRODUCT_CATEGORY_FIXES.get(
            product["id"], PLACEHOLDER_CATEGORY_MAP.get(current_category, current_category)
        )
        values = {}
        if final_category != current_category:
            values["categ_id"] = final_category
        if product["active"] and product["sale_ok"] and product["x_website_category_ids"] != [final_category]:
            values["x_website_category_ids"] = [(6, 0, [final_category])]
        if values:
            proposed.append({"id": product["id"], "name": product["name"], "values": values})

    print(json.dumps({"mode": "apply" if args.apply else "dry-run", "before": before, "updates": len(proposed)}, indent=2))
    if not args.apply:
        print(json.dumps(proposed, indent=2))
        return

    for change in proposed:
        call("product.template", "write", [[change["id"]], change["values"]])

    # Delete placeholder category records after every product reference has been
    # migrated. Skip instead of forcing deletion if another model still uses one.
    deleted = []
    skipped = []
    for category_id in PLACEHOLDER_CATEGORY_MAP:
        try:
            call("product.category", "unlink", [[category_id]])
            deleted.append(category_id)
        except Exception as exc:
            skipped.append({"id": category_id, "error": str(exc)[:300]})

    verified = call(
        "product.template", "search_read",
        [[("active", "=", True), ("sale_ok", "=", True)]],
        {"fields": ["categ_id", "x_website_category_ids"]},
    )
    after = {
        "active_shop_products": len(verified),
        "missing": sum(not p["x_website_category_ids"] for p in verified),
        "multiple": sum(len(p["x_website_category_ids"]) > 1 for p in verified),
        "mismatch": sum(
            bool(p["x_website_category_ids"])
            and p["categ_id"][0] not in p["x_website_category_ids"]
            for p in verified
        ),
    }
    print(json.dumps({"after": after, "deleted_placeholder_categories": deleted, "skipped": skipped}, indent=2))


if __name__ == "__main__":
    main()
