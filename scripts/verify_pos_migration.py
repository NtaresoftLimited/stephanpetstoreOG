"""Independent record-by-record check of the Odoo 18 -> 20 POS/inventory migration.

Reads both databases directly with SQL (read-only transactions); it does not use the import
script's own bookkeeping except the product key table it wrote (ir.model.data module
stephans_pos_migration), which is itself checked by comparing product codes and names.

    sudo -u postgres python3 verify_pos_migration.py [Stephans] [stephans_odoo20]

Prints a summary per area and up to 15 examples of every kind of difference.
"""
import collections
import sys

import psycopg2
import psycopg2.extras

SRC_DB = sys.argv[1] if len(sys.argv) > 1 else "Stephans"
DST_DB = sys.argv[2] if len(sys.argv) > 2 else "stephans_odoo20"
CONFIG_MAP = {1: "Stephan's Pet Store Masaki", 5: "Stephan's Pet Store Masaki",
              6: "Stephan's Pet Store Masaki", 7: "Stephan's Pet Store Mikocheni"}
CASH_BY_CONFIG = {"Stephan's Pet Store Masaki": "Cash Masaki",
                  "Stephan's Pet Store Mikocheni": "Cash Mikocheni"}
WAREHOUSES = ("MASAK", "MBS", "MIKOC")
EPS = 0.005


def connect(db):
    conn = psycopg2.connect(dbname=db)
    conn.set_session(readonly=True)
    return conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)


src, dst = connect(SRC_DB), connect(DST_DB)
problems = collections.defaultdict(list)


def report(kind, detail):
    problems[kind].append(detail)


def q(cur, sql, args=None):
    cur.execute(sql, args)
    rows = cur.fetchall()
    for row in rows:  # translated names come back as jsonb dicts on one side only
        for key in ("cfg", "employee", "mname", "complete_name"):
            if isinstance(row.get(key), dict):
                row[key] = txt(row[key])
    return rows


def txt(value):
    """Translated jsonb names -> plain text."""
    if isinstance(value, dict):
        return value.get("en_US") or next(iter(value.values()), "")
    return value or ""


def differs(a, b):
    if isinstance(a, float) or isinstance(b, float):
        return abs((a or 0.0) - (b or 0.0)) > EPS
    return (a or None) != (b or None)


# ---------------------------------------------------------------- product mapping
pmap = {int(r["name"].rsplit("_", 1)[1]): r["res_id"] for r in q(dst, """
    select name, res_id from ir_model_data
    where module='stephans_pos_migration' and model='product.product' and name like 'product_product_%%'""")}

PRODUCT_SQL = """
    select pp.id, pp.default_code, pp.barcode, pp.active and pt.active as active, pt.name,
           pt.list_price::float, pt.available_in_pos, pt.type, pt.is_storable
    from product_product pp join product_template pt on pt.id = pp.product_tmpl_id"""
sp = {r["id"]: r for r in q(src, PRODUCT_SQL)}
dp = {r["id"]: r for r in q(dst, PRODUCT_SQL)}
s_cost = {r["pid"]: r["cost"] for r in q(src, """
    select (regexp_match(res_id, '[0-9]+$'))[1]::int pid, value_float::float cost
    from ir_property where name='standard_price' and res_id like 'product.product,%%'""")} \
    if q(src, "select 1 from information_schema.tables where table_name='ir_property'") else {}

# Duplicate targets: two different Odoo 18 products mapped onto one Odoo 20 product.
by_target = collections.defaultdict(list)
for s_id, d_id in pmap.items():
    by_target[d_id].append(s_id)
for d_id, s_ids in by_target.items():
    if len(s_ids) > 1:
        codes = {sp[s]["default_code"] for s in s_ids if s in sp}
        report("product: several Odoo 18 products merged into one",
               "%s -> %s %s codes=%s" % (s_ids, d_id, txt(dp.get(d_id, {}).get("name")), codes))

for s_id, d_id in pmap.items():
    s, d = sp.get(s_id), dp.get(d_id)
    if not s or not d:
        report("product: mapping points at a missing record", "%s -> %s" % (s_id, d_id))
        continue
    if s["default_code"] and d["default_code"] and s["default_code"] != d["default_code"]:
        report("product: product code differs", "%s %s / %s %s" % (s["default_code"], txt(s["name"]), d["default_code"], txt(d["name"])))
    if not txt(d["name"]).strip().lower().startswith(txt(s["name"]).strip().lower()):
        report("product: name differs (review)", "%r -> %r" % (txt(s["name"]), txt(d["name"])))
    if s["active"] and s["available_in_pos"]:
        if differs(s["list_price"], d["list_price"]):
            report("product: sale price differs (sellable)", "%s %s: %s -> %s" % (s["default_code"], txt(s["name"]), s["list_price"], d["list_price"]))
        if (s["barcode"] or None) != (d["barcode"] or None):
            report("product: barcode differs (sellable)", "%s %s: %s -> %s" % (s["default_code"], txt(s["name"]), s["barcode"], d["barcode"]))
        if not d["active"] or not d["available_in_pos"]:
            report("product: sellable in 18 but not in 20 POS", "%s %s active=%s pos=%s" % (s["default_code"], txt(s["name"]), d["active"], d["available_in_pos"]))

# Sellable Odoo 18 products that never made it into the map (no sale, no stock) still need
# to exist in Odoo 20 for the tills: look them up by code.
dst_codes = {r["default_code"]: r for r in dp.values() if r["default_code"]}
dst_barcodes = {r["barcode"]: r for r in dp.values() if r["barcode"]}
dst_names = collections.defaultdict(list)
for r in dp.values():
    if r["active"] and r["available_in_pos"]:
        dst_names[txt(r["name"]).strip().lower()].append(r)
for s in sp.values():
    if s["id"] in pmap or not (s["active"] and s["available_in_pos"]):
        continue
    d = dst_codes.get(s["default_code"]) or dst_barcodes.get(s["barcode"])
    if not d and not s["default_code"] and not s["barcode"] and dst_names.get(txt(s["name"]).strip().lower()):
        continue  # code-less variant: present by name (prices differ per variant, not checked)
    if not d:
        report("catalogue: sellable Odoo 18 product missing in Odoo 20", "%s %s %s" % (s["default_code"], s["barcode"], txt(s["name"])))
    elif differs(s["list_price"], d["list_price"]):
        report("catalogue: sale price differs (not in history)", "%s %s: %s -> %s" % (s["default_code"], txt(s["name"]), s["list_price"], d["list_price"]))

# ---------------------------------------------------------------- sessions
S_SESS = {r["id"]: r for r in q(src, """
    select s.id, s.name, s.config_id, s.start_at, s.stop_at, u.login
    from pos_session s left join res_users u on u.id=s.user_id""")}
d_sess_key = {int(r["name"].rsplit("_", 1)[1]): r["res_id"] for r in q(dst, """
    select name, res_id from ir_model_data where module='stephans_pos_migration' and model='pos.session'""")}
D_SESS = {r["id"]: r for r in q(dst, """
    select s.id, s.name, s.state, c.name cfg, s.start_at, s.stop_at, u.login
    from pos_session s join pos_config c on c.id=s.config_id left join res_users u on u.id=s.user_id""")}
src_sessions_with_orders = {r["session_id"] for r in q(src, "select distinct session_id from pos_order")}
for s_id in src_sessions_with_orders:
    s = S_SESS[s_id]
    d = D_SESS.get(d_sess_key.get(s_id))
    if not d:
        report("session: missing", s["name"])
        continue
    for field in ("name", "start_at", "stop_at", "login"):
        if differs(s[field], d[field]) and not (field == "stop_at" and not s["stop_at"]):
            report("session: %s differs" % field, "%s: %s -> %s" % (s["name"], s[field], d[field]))
    if CONFIG_MAP.get(s["config_id"]) != d["cfg"]:
        report("session: wrong till", "%s: config %s -> %s" % (s["name"], s["config_id"], d["cfg"]))
    if d["state"] != "closed":
        report("session: not closed", d["name"])

# ---------------------------------------------------------------- orders
ORDER_SQL = """
    select o.id, o.uuid, o.name, o.pos_reference, o.date_order, o.state,
           o.amount_total::float, o.amount_tax::float, o.amount_paid::float, o.amount_return::float,
           o.session_id, u.login, o.partner_id, e.name employee, c.name cfg
    from pos_order o left join res_users u on u.id=o.user_id
    left join hr_employee e on e.id=o.employee_id
    join pos_session s on s.id=o.session_id join pos_config c on c.id=s.config_id"""
SO = {r["uuid"]: r for r in q(src, ORDER_SQL)}
DO = {r["uuid"]: r for r in q(dst, ORDER_SQL)}
dst_order_ids = {r["id"] for r in DO.values()}
for uuid in set(DO) - set(SO):
    report("order: in Odoo 20 but not in Odoo 18 (test/extra)", "%s %s" % (DO[uuid]["name"], DO[uuid]["date_order"]))
for uuid, s in SO.items():
    d = DO.get(uuid)
    if not d:
        report("order: missing in Odoo 20", "%s %s" % (s["name"], s["amount_total"]))
        continue
    for field in ("name", "pos_reference", "date_order", "amount_total",
                  "amount_tax", "amount_paid", "amount_return", "login", "employee"):
        if differs(s[field], d[field]):
            report("order: %s differs" % field, "%s: %s -> %s" % (s["name"], s[field], d[field]))
    expected_state = "cancel" if s["state"] == "cancel" else "done"
    if d["state"] != expected_state:
        report("order: state", "%s: %s -> %s" % (s["name"], s["state"], d["state"]))
    if d["cfg"] != CONFIG_MAP.get(S_SESS[s["session_id"]]["config_id"]):
        report("order: wrong till", "%s -> %s" % (s["name"], d["cfg"]))
    if d["session_id"] != d_sess_key.get(s["session_id"]):
        report("order: wrong session", s["name"])

# ---------------------------------------------------------------- lines
LINE_SQL = """
    select l.id, o.uuid, l.product_id, l.qty::float, l.price_unit::float, l.discount::float,
           l.price_subtotal::float, l.price_subtotal_incl::float, l.full_product_name,
           l.refunded_orderline_id
    from pos_order_line l join pos_order o on o.id=l.order_id order by l.id"""
SL, DL = collections.defaultdict(list), collections.defaultdict(list)
for r in q(src, LINE_SQL):
    SL[r["uuid"]].append(r)
for r in q(dst, LINE_SQL):
    DL[r["uuid"]].append(r)
line_pairs = {}
for uuid, s_lines in SL.items():
    d_lines = DL.get(uuid, [])
    name = SO[uuid]["name"]
    if len(s_lines) != len(d_lines):
        report("lines: count differs", "%s: %d -> %d" % (name, len(s_lines), len(d_lines)))
        continue
    for s, d in zip(s_lines, d_lines):
        line_pairs[s["id"]] = d["id"]
        if pmap.get(s["product_id"]) != d["product_id"]:
            report("lines: product differs", "%s: %s -> %s" % (name, s["full_product_name"], d["full_product_name"]))
        for field in ("qty", "price_unit", "discount", "price_subtotal", "price_subtotal_incl", "full_product_name"):
            if differs(s[field], d[field]):
                report("lines: %s differs" % field, "%s %s: %s -> %s" % (name, s["full_product_name"], s[field], d[field]))
d_line_refund = {r["id"]: r["refunded_orderline_id"] for rows in DL.values() for r in rows}
for rows in SL.values():
    for s in rows:
        if s["refunded_orderline_id"]:
            if d_line_refund.get(line_pairs.get(s["id"])) != line_pairs.get(s["refunded_orderline_id"]):
                report("lines: refund link missing/wrong", "line %s" % s["id"])
        elif d_line_refund.get(line_pairs.get(s["id"])):
            report("lines: unexpected refund link", "line %s" % s["id"])

# ---------------------------------------------------------------- payments
PAY_SQL = """
    select o.uuid, m.name mname, p.amount::float, p.payment_date, p.is_change, c.name cfg
    from pos_payment p join pos_order o on o.id=p.pos_order_id
    join pos_payment_method m on m.id=p.payment_method_id
    join pos_session s on s.id=o.session_id join pos_config c on c.id=s.config_id"""
SPAY, DPAY = collections.defaultdict(list), collections.defaultdict(list)
for r in q(src, PAY_SQL):
    SPAY[r["uuid"]].append(r)
for r in q(dst, PAY_SQL):
    DPAY[r["uuid"]].append(r)
method_totals = collections.defaultdict(lambda: [0.0, 0.0])
for uuid in set(SPAY) | set(DPAY):
    if uuid not in SO:
        continue
    cfg = DO[uuid]["cfg"] if uuid in DO else None

    def norm_src(p):
        name = txt(p["mname"])
        return CASH_BY_CONFIG.get(cfg) if name == "Cash" else name

    s_set = sorted((norm_src(p), round(p["amount"], 2), str(p["payment_date"]), bool(p["is_change"])) for p in SPAY[uuid])
    d_set = sorted((txt(p["mname"]), round(p["amount"], 2), str(p["payment_date"]), bool(p["is_change"])) for p in DPAY[uuid])
    if s_set != d_set:
        report("payments: differ", "%s: %s -> %s" % (SO[uuid]["name"], s_set, d_set))
    for p in s_set:
        method_totals[p[0]][0] += p[1]
    for p in d_set:
        method_totals[p[0]][1] += p[1]

# ---------------------------------------------------------------- stock
STOCK_SQL = """
    select w.code, q.product_id, sum(q.quantity)::float qty
    from stock_quant q join stock_location l on l.id=q.location_id
    join stock_warehouse w on l.parent_path like (select parent_path from stock_location where id=w.lot_stock_id) || '%%'
    join product_product pp on pp.id=q.product_id join product_template pt on pt.id=pp.product_tmpl_id
    where pt.type <> 'service' group by 1, 2"""
s_stock = {(r["code"], r["product_id"]): r["qty"] for r in q(src, STOCK_SQL) if r["code"] in WAREHOUSES}
d_stock = {(r["code"], r["product_id"]): r["qty"] for r in q(dst, STOCK_SQL) if r["code"] in WAREHOUSES}
expected = collections.defaultdict(float)
for (code, s_pid), qty in s_stock.items():
    if s_pid not in pmap:
        if round(qty, 4):
            report("stock: Odoo 18 product with stock has no mapping", "%s %s %s" % (code, s_pid, qty))
        continue
    expected[(code, pmap[s_pid])] += qty
for key in set(expected) | set(d_stock):
    if abs(expected.get(key, 0.0) - d_stock.get(key, 0.0)) > 0.0001:
        code, d_pid = key
        report("stock: quantity differs", "%s %s %s: %s -> %s" % (code, dp.get(d_pid, {}).get("default_code"),
               txt(dp.get(d_pid, {}).get("name")), expected.get(key, 0.0), d_stock.get(key, 0.0)))
other = q(dst, """select l.complete_name, count(*) n, sum(q.quantity)::float qty from stock_quant q
    join stock_location l on l.id=q.location_id where l.usage='internal' and q.quantity<>0
    and not exists (select 1 from stock_warehouse w join stock_location ls on ls.id=w.lot_stock_id
                    where l.parent_path like ls.parent_path || '%%') group by 1""")
for r in other:
    report("stock: Odoo 20 stock outside the 3 warehouse stock locations", "%s rows=%s qty=%s" % (r["complete_name"], r["n"], r["qty"]))

# ---------------------------------------------------------------- side effects of the import
for sql, label in (
    ("select count(*) n from account_move m join pos_order o on o.account_move=m.id", "journal entries linked to POS orders"),
    ("select count(*) n from stock_picking p join pos_order o on o.id=p.pos_order_id", "stock pickings linked to POS orders"),
    ("select count(*) n from pos_order where uuid is null", "orders without uuid"),
    ("select count(*) n from (select uuid from pos_order group by uuid having count(*)>1) x", "duplicate order uuids"),
    ("select count(*) n from pos_session where state<>'closed'", "open sessions"),
):
    try:
        n = q(dst, sql)[0]["n"]
    except psycopg2.Error as exc:
        dst.connection.rollback()
        n = "n/a (%s)" % str(exc).splitlines()[0]
    print("SIDE-EFFECT %-40s %s" % (label, n))

# ---------------------------------------------------------------- summary
print()
print("PRODUCTS mapped=%d  ORDERS src=%d dst=%d  LINES src=%d dst=%d  SESSIONS src(with orders)=%d" % (
    len(pmap), len(SO), len(DO), sum(map(len, SL.values())), sum(map(len, DL.values())), len(src_sessions_with_orders)))
print("TOTALS src=%.2f dst=%.2f" % (sum(o["amount_total"] for o in SO.values()),
                                    sum(o["amount_total"] for o in DO.values() if o["uuid"] in SO)))
for name, (a, b) in sorted(method_totals.items(), key=lambda x: str(x[0])):
    print("PAYMENT %-16s src=%16.2f dst=%16.2f %s" % (name, a, b, "" if abs(a - b) < EPS else "<-- DIFF"))
print("STOCK rows src=%d dst=%d" % (len(expected), len([k for k, v in d_stock.items() if round(v, 4)])))
print()
if not problems:
    print("NO DIFFERENCES")
for kind in sorted(problems):
    items = problems[kind]
    print("== %s: %d" % (kind, len(items)))
    for item in items[:15]:
        print("   ", item)
