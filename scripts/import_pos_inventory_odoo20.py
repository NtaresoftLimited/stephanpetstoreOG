"""Import Odoo 18 POS history and current stock into Odoo 20.

Input: /var/tmp/stephans_pos_inventory.json.gz written by export_pos_inventory_odoo18.py.

Run inside `odoo-bin shell` on the Odoo 20 database:
    MIG_COMMIT=1 odoo-bin shell -c /etc/odoo/odoo20_stephans.conf -d stephans_odoo20 --no-http < import_pos_inventory_odoo20.py
Without MIG_COMMIT=1 everything runs and is then rolled back (dry run).

What it does
  1. Products: maps every product sold or in stock onto the Odoo 20 catalogue (via the
     stephans_product_migration template ids, then product code); products that no longer
     exist are created archived, so old sales keep their product.
  2. Users: cashiers missing in Odoo 20 are created archived (no password), so each order
     keeps its cashier. Activate them and set passwords at go-live.
  3. POS history: sessions and orders are recreated as closed history with their original
     names, receipt numbers, dates, lines and payments. No stock moves or journal entries are
     generated (those happened in Odoo 18); stock comes from step 4.
  4. Stock: sets on-hand quantities in MASAK/Stock, MBS/Stock and MIKOC/Stock to the Odoo 18
     figures (an inventory adjustment); products absent from the export are set to 0.

Re-runnable: products and sessions are keyed in ir.model.data (module stephans_pos_migration),
orders by their Odoo 18 uuid; already-imported records are skipped, stock is re-set.
"""
import collections
import gzip
import json
import os

INPUT = "/var/tmp/stephans_pos_inventory.json.gz"
MODULE = "stephans_pos_migration"
COMMIT = os.environ.get("MIG_COMMIT") == "1"

# Odoo 18 pos.config id -> Odoo 20 pos.config name. Configs 1 and 6 were earlier Masaki tills.
CONFIG_MAP = {
    1: "Stephan's Pet Store Masaki",
    5: "Stephan's Pet Store Masaki",
    6: "Stephan's Pet Store Masaki",
    7: "Stephan's Pet Store Mikocheni",
}
# Odoo 18 payment method name -> Odoo 20 name ("Cash" depends on the till).
CASH_BY_CONFIG = {
    "Stephan's Pet Store Masaki": "Cash Masaki",
    "Stephan's Pet Store Mikocheni": "Cash Mikocheni",
}
METHOD_MAP = {"Card": "Card", "Selcom": "Selcom"}

with gzip.open(INPUT, "rt", encoding="utf-8") as stream:
    data = json.load(stream)

# install_mode skips the grooming "picture/price required" product checks (archived legacy
# products have no picture), as the earlier product import did.
ctx = dict(active_test=False, tracking_disable=True, mail_create_nolog=True, mail_notrack=True,
           mail_create_nosubscribe=True, install_mode=True)

# No outbound HTTP during the migration (grooming sends WhatsApp messages on product create).
import requests  # noqa: E402


def _blocked(*args, **kwargs):
    raise RuntimeError("outbound HTTP disabled during migration")


requests.post = requests.get = requests.request = _blocked
requests.Session.request = _blocked
IMD = env["ir.model.data"].sudo()
stats = collections.Counter()
warnings = []


def xmlid_get(name, model):
    rec = IMD.search([("module", "=", MODULE), ("name", "=", name)], limit=1)
    return env[model].sudo().with_context(**ctx).browse(rec.res_id).exists() if rec else env[model]


def xmlid_set(name, record):
    rec = IMD.search([("module", "=", MODULE), ("name", "=", name)], limit=1)
    vals = {"module": MODULE, "name": name, "model": record._name, "res_id": record.id, "noupdate": True}
    rec.write(vals) if rec else IMD.create(vals)


def path_record(model_name, path):
    parent = env[model_name]
    for name in path:
        domain = [("name", "=", name), ("parent_id", "=", parent.id or False)]
        record = env[model_name].sudo().search(domain, limit=1)
        if not record:
            record = env[model_name].sudo().create({"name": name, "parent_id": parent.id or False})
        parent = record
    return parent


# ---------------------------------------------------------------------------------------------
# 1. Products
# ---------------------------------------------------------------------------------------------
Product = env["product.product"].sudo().with_context(**ctx)
Template = env["product.template"].sudo().with_context(**ctx)
product_map = {}

for src in data["products"]:
    key = "product_product_%d" % src["id"]
    dest = xmlid_get(key, "product.product")
    how = "xmlid"
    if not dest:
        how = "template"
        tmpl_data = IMD.search([("module", "=", "stephans_product_migration"),
                                ("name", "=", "product_template_%d" % src["template_id"])], limit=1)
        tmpl = Template.browse(tmpl_data.res_id).exists() if tmpl_data else Template
        if tmpl:
            combination = sorted([list(c) for c in src["combination"]])
            variants = tmpl.with_context(active_test=False).product_variant_ids
            for variant in variants:
                comb = sorted([[v.attribute_id.name, v.name] for v in variant.product_template_attribute_value_ids])
                if comb == combination:
                    dest = variant
                    break
            if not dest and len(variants) == 1 and not combination:
                dest = variants
            # Never map onto a variant with a different product code (distinct products).
            if dest and src["default_code"] and dest.default_code and dest.default_code != src["default_code"]:
                dest = Product
    if not dest and src["default_code"]:
        how = "code"
        found = Product.search([("default_code", "=", src["default_code"])])
        if len(found) == 1:
            dest = found
    if not dest:
        how = "created"
        vals = {
            "name": src["display_name"] if src["combination"] else src["name"],
            "default_code": src["default_code"] or False,
            "list_price": src["list_price"],
            "standard_price": src["standard_price"],
            "type": "service" if src["type"] == "service" else "consu",
            "is_storable": bool(src["is_storable"]) and src["type"] != "service",
            "available_in_pos": src["available_in_pos"],
            "sale_ok": True,
            "active": src["active"],
            "taxes_id": [(6, 0, [])],
        }
        if src["category"]:
            vals["categ_id"] = path_record("product.category", src["category"]).id
        uom = env["uom.uom"].sudo().search([("name", "=", src["uom"])], limit=1)
        if uom:
            vals["uom_id"] = uom.id
        if "approval_state" in Template._fields:
            vals["approval_state"] = "approved"
        if src["pos_categories"]:
            vals["pos_categ_ids"] = [(6, 0, [path_record("pos.category", p).id for p in src["pos_categories"]])]
        dest = Template.create(vals).product_variant_ids[:1]
        if not src["active"]:
            dest.active = False
        else:
            print("CREATED_ACTIVE", src["id"], src["default_code"], src["display_name"])
    xmlid_set(key, dest)
    if dest.id in product_map.values():
        print("MERGED", src["id"], src["display_name"], "->", dest.id, dest.display_name)
    product_map[src["id"]] = dest.id
    stats["product_" + how] += 1

# product_auto_code refuses POS lines for unapproved products. Everything in the history was
# really sold in Odoo 18, so approve exactly those products.
sold_ids = {product_map[l["product_id"]] for o in data["orders"] for l in o["lines"]}
if "approval_state" in Template._fields:
    unapproved = Product.browse(sorted(sold_ids)).product_tmpl_id.filtered(lambda t: t.approval_state != "approved")
    for tmpl in unapproved:
        print("APPROVED_FOR_HISTORY", tmpl.id, tmpl.display_name)
    unapproved.write({"approval_state": "approved"})
    stats["approved_for_history"] = len(unapproved)

# ---------------------------------------------------------------------------------------------
# 2. Users
# ---------------------------------------------------------------------------------------------
Users = env["res.users"].sudo().with_context(**ctx)
admin = env.ref("base.user_admin")
pos_user_group = env.ref("point_of_sale.group_pos_user")
logins = {s["user_login"] for s in data["sessions"]} | {o["user_login"] for o in data["orders"]}
user_map = {}
for login in sorted(filter(None, logins)):
    user = Users.search([("login", "=", login)], limit=1)
    if not user:
        name = login.split("@")[0].replace(".", " ").title()
        user = Users.create({"name": name, "login": login, "email": login,
                             "group_ids": [(4, pos_user_group.id)]})
        user.active = False
        stats["users_created"] += 1
    user_map[login] = user.id

# ---------------------------------------------------------------------------------------------
# 3. POS sessions and orders (closed history)
# ---------------------------------------------------------------------------------------------
Config = env["pos.config"].sudo()
Session = env["pos.session"].sudo().with_context(**ctx)
Order = env["pos.order"].sudo().with_context(**ctx)

configs = {}
for src_id, name in CONFIG_MAP.items():
    config = Config.search([("name", "=", name)], limit=1)
    if not config:
        raise SystemExit("Odoo 20 POS config not found: %s" % name)
    if config.current_session_id:
        raise SystemExit("Close the open session on %s before importing." % name)
    configs[src_id] = config


def method_for(config, src_name):
    target = CASH_BY_CONFIG[config.name] if src_name == "Cash" else METHOD_MAP.get(src_name)
    method = config.payment_method_ids.filtered(lambda m: m.name == target)[:1]
    if not method:
        raise SystemExit("Payment method %r (from %r) is not on %s" % (target, src_name, config.name))
    return method


session_map = {}
for src in data["sessions"]:
    key = "pos_session_%d" % src["id"]
    session = xmlid_get(key, "pos.session")
    if not session:
        config = configs.get(src["config_id"])
        if not config:
            warnings.append("session %s: no target till for config %s" % (src["name"], src["config_id"]))
            continue
        session = Session.create({
            "config_id": config.id,
            "user_id": user_map.get(src["user_login"], admin.id),
            "start_at": src["start_at"] or False,
        })
        session.write({"name": src["name"], "state": "closed",
                       "stop_at": src["stop_at"] or src["start_at"] or False})
        xmlid_set(key, session)
        stats["sessions_created"] += 1
    else:
        stats["sessions_existing"] += 1
    session_map[src["id"]] = session

existing_uuids = set(Order.search([("uuid", "in", [o["uuid"] for o in data["orders"] if o["uuid"]])]).mapped("uuid"))
line_map = {}
for index, src in enumerate(data["orders"], 1):
    if src["uuid"] in existing_uuids:
        stats["orders_existing"] += 1
        continue
    session = session_map.get(src["session_id"])
    if not session:
        warnings.append("order %s skipped: session not imported" % src["name"])
        continue
    config = session.config_id
    lines = []
    for line in src["lines"]:
        lines.append((0, 0, {
            "name": line["name"],
            "product_id": product_map[line["product_id"]],
            "full_product_name": line["full_product_name"],
            "qty": line["qty"],
            "price_unit": line["price_unit"],
            "discount": line["discount"],
            "price_subtotal": line["price_subtotal"],
            "price_subtotal_incl": line["price_subtotal_incl"],
            "customer_note": line["customer_note"] or False,
            "tax_ids": [(6, 0, [])],
        }))
    payments = [(0, 0, {
        "payment_method_id": method_for(config, p["method_name"]).id,
        "amount": p["amount"],
        "payment_date": p["payment_date"] or src["date_order"],
        "is_change": bool(p["is_change"]),
    }) for p in src["payments"]]
    order = Order.create({
        "session_id": session.id,
        "name": src["name"],
        "uuid": src["uuid"],
        "pos_reference": src["pos_reference"],
        "tracking_number": src["tracking_number"] or False,
        "sequence_number": src["sequence_number"] or 0,
        "date_order": src["date_order"],
        "user_id": user_map.get(src["user_login"], admin.id),
        "amount_total": src["amount_total"],
        "amount_tax": src["amount_tax"],
        "amount_paid": src["amount_paid"],
        "amount_return": src["amount_return"],
        "state": "draft",
        "lines": lines,
        "payment_ids": payments,
    })
    # Keep the stored Odoo 18 totals (the create may recompute them from the lines).
    order.write({"amount_total": src["amount_total"], "amount_tax": src["amount_tax"],
                 "amount_paid": src["amount_paid"], "amount_return": src["amount_return"],
                 "state": "cancel" if src["state"] == "cancel" else "done"})
    for src_line, dest_line in zip(src["lines"], order.lines.sorted("id")):
        line_map[src_line["id"]] = dest_line
    stats["orders_created"] += 1
    if index % 500 == 0:
        print("ORDERS", index)

# Link refund lines to the lines they refunded.
for src in data["orders"]:
    for line in src["lines"]:
        if line["refunded_orderline_id"] and line["id"] in line_map and line["refunded_orderline_id"] in line_map:
            line_map[line["id"]].refunded_orderline_id = line_map[line["refunded_orderline_id"]].id
            stats["refund_links"] += 1

# ---------------------------------------------------------------------------------------------
# 4. Stock on hand
# ---------------------------------------------------------------------------------------------
Quant = env["stock.quant"].sudo().with_context(inventory_mode=True, **ctx)
warehouses = {w.code: w for w in env["stock.warehouse"].sudo().search([])}
wanted = collections.defaultdict(float)
for row in data["stock"]:
    wanted[(row["warehouse"], product_map[row["product_id"]])] += row["quantity"]

to_apply = Quant
for code in ("MASAK", "MBS", "MIKOC"):
    location = warehouses[code].lot_stock_id
    current = Quant.search([("location_id", "=", location.id)])
    seen = set()
    for quant in current:
        target = wanted.get((code, quant.product_id.id), 0.0)
        if (quant.product_id.id in seen):
            target = 0.0  # extra quants (lots/packages) of the same product
        seen.add(quant.product_id.id)
        if round(quant.quantity - target, 4):
            quant.inventory_quantity = target
            to_apply |= quant
    for (wh, product_id), qty in wanted.items():
        if wh != code or product_id in seen:
            continue
        product = Product.browse(product_id)
        if not product.is_storable:
            product.product_tmpl_id.is_storable = True
            stats["made_storable"] += 1
        to_apply |= Quant.create({"product_id": product_id, "location_id": location.id, "inventory_quantity": qty})
if to_apply:
    to_apply._apply_inventory()
stats["stock_adjusted"] = len(to_apply)

# ---------------------------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------------------------
env.flush_all()
imported = Order.search([("uuid", "in", [o["uuid"] for o in data["orders"]])])
print("CHECK orders", len(imported), "of", len(data["orders"]))
print("CHECK total", round(sum(imported.mapped("amount_total")), 2), "source", round(sum(o["amount_total"] for o in data["orders"]), 2))
print("CHECK lines", sum(len(o.lines) for o in imported), "of", sum(len(o["lines"]) for o in data["orders"]))
by_cfg = collections.defaultdict(float)
for o in imported:
    by_cfg[o.config_id.name] += o.amount_total
print("CHECK per till", {k: round(v, 2) for k, v in by_cfg.items()})
mismatch = 0
for (code, product_id), qty in wanted.items():
    have = sum(Quant.search([("location_id", "=", warehouses[code].lot_stock_id.id), ("product_id", "=", product_id)]).mapped("quantity"))
    if round(have - qty, 4):
        mismatch += 1
print("CHECK stock rows", len(wanted), "mismatches", mismatch)
print("STATS", dict(stats))
for w in warnings[:20]:
    print("WARN", w)

if COMMIT:
    env.cr.commit()
    print("COMMITTED")
else:
    env.cr.rollback()
    print("DRY RUN - rolled back")
