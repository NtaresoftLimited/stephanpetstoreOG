"""Export POS history and current stock from Odoo 18 (read only).

Run inside `odoo-bin shell` on the Odoo 18 production database:
    odoo-bin shell -c /etc/odoo/odoo_stephans.conf -d Stephans --no-http < export_pos_inventory_odoo18.py

Writes /var/tmp/stephans_pos_inventory.json.gz for import_pos_inventory_odoo20.py.
Nothing is written to the database (the transaction is rolled back at the end).
"""
import gzip
import json

OUTPUT = "/var/tmp/stephans_pos_inventory.json.gz"
STOCK_WAREHOUSES = ("MASAK", "MBS", "MIKOC")


def dt(value):
    return value.isoformat(sep=" ") if value else False


def hierarchy(record):
    names = []
    while record:
        names.append(record.name)
        record = record.parent_id
    return list(reversed(names))


def opt(record, name, default=False):
    return record[name] if name in record._fields else default


Product = env["product.product"].sudo().with_context(active_test=False)
Order = env["pos.order"].sudo().with_context(active_test=False)
Session = env["pos.session"].sudo().with_context(active_test=False)

# --- stock on hand per warehouse stock location (children included) ---------------------------
stock = []
for code in STOCK_WAREHOUSES:
    warehouse = env["stock.warehouse"].sudo().search([("code", "=", code)], limit=1)
    if not warehouse:
        raise SystemExit("Warehouse %s not found" % code)
    groups = env["stock.quant"].sudo().read_group(
        [("location_id", "child_of", warehouse.lot_stock_id.id), ("product_id.type", "!=", "service")],
        ["product_id", "quantity:sum"], ["product_id"],
    )
    for group in groups:
        if round(group["quantity"], 4):
            stock.append({"warehouse": code, "product_id": group["product_id"][0], "quantity": group["quantity"]})

# --- POS sessions and orders -----------------------------------------------------------------
orders = Order.search([], order="id")
sessions = Session.search([("id", "in", orders.mapped("session_id").ids)], order="id")

payload = {
    "source_database": env.cr.dbname,
    "stock": stock,
    "sessions": [],
    "orders": [],
    "products": [],
}

for session in sessions:
    payload["sessions"].append({
        "id": session.id,
        "name": session.name,
        "config_id": session.config_id.id,
        "config_name": session.config_id.name,
        "user_login": session.user_id.login,
        "start_at": dt(session.start_at),
        "stop_at": dt(session.stop_at),
        "state": session.state,
    })

for index, order in enumerate(orders, 1):
    payload["orders"].append({
        "id": order.id,
        "uuid": opt(order, "uuid"),
        "name": order.name,
        "pos_reference": order.pos_reference,
        "tracking_number": opt(order, "tracking_number"),
        "sequence_number": opt(order, "sequence_number", 0),
        "session_id": order.session_id.id,
        "date_order": dt(order.date_order),
        "user_login": order.user_id.login,
        "state": order.state,
        "amount_total": order.amount_total,
        "amount_tax": order.amount_tax,
        "amount_paid": order.amount_paid,
        "amount_return": order.amount_return,
        "note": opt(order, "general_note") or opt(order, "note") or False,
        "lines": [{
            "id": line.id,
            "name": line.name,
            "product_id": line.product_id.id,
            "full_product_name": line.full_product_name or line.product_id.display_name,
            "qty": line.qty,
            "price_unit": line.price_unit,
            "discount": line.discount,
            "price_subtotal": line.price_subtotal,
            "price_subtotal_incl": line.price_subtotal_incl,
            "customer_note": opt(line, "customer_note"),
            "refunded_orderline_id": line.refunded_orderline_id.id if "refunded_orderline_id" in line._fields else False,
        } for line in order.lines],
        "payments": [{
            "method_id": payment.payment_method_id.id,
            "method_name": payment.payment_method_id.name,
            "amount": payment.amount,
            "payment_date": dt(payment.payment_date),
            "is_change": opt(payment, "is_change"),
        } for payment in order.payment_ids],
    })
    if index % 500 == 0:
        print("ORDERS", index)

# --- every product referenced by stock or order lines ------------------------------------------
product_ids = {row["product_id"] for row in stock}
product_ids |= {line["product_id"] for order in payload["orders"] for line in order["lines"]}
for product in Product.browse(sorted(product_ids)):
    template = product.product_tmpl_id
    payload["products"].append({
        "id": product.id,
        "template_id": template.id,
        "name": template.name,
        "display_name": product.display_name,
        "default_code": product.default_code or False,
        "barcode": product.barcode or False,
        "combination": sorted([(v.attribute_id.name, v.name) for v in product.product_template_attribute_value_ids]),
        "list_price": template.list_price,
        "standard_price": product.standard_price,
        "type": template.type,
        "is_storable": opt(template, "is_storable", template.type == "product"),
        "active": bool(product.active and template.active),
        "available_in_pos": template.available_in_pos,
        "category": hierarchy(template.categ_id) if template.categ_id else [],
        "uom": template.uom_id.name,
        "pos_categories": [hierarchy(c) for c in template.pos_categ_ids] if "pos_categ_ids" in template._fields else [],
    })

with gzip.open(OUTPUT, "wt", encoding="utf-8") as stream:
    json.dump(payload, stream, ensure_ascii=False)

env.cr.rollback()
print("EXPORT_COMPLETE", OUTPUT, "products=%d stock_rows=%d sessions=%d orders=%d lines=%d" % (
    len(payload["products"]), len(stock), len(payload["sessions"]), len(payload["orders"]),
    sum(len(o["lines"]) for o in payload["orders"]),
))
print("TOTAL_SALES", round(sum(o["amount_total"] for o in payload["orders"]), 2))
