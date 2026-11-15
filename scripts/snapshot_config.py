"""Snapshot functional configuration (read only) for comparing Odoo 18 and Odoo 20.

odoo-bin shell -c <conf> -d <db> --no-http < snapshot_config.py   (writes /var/tmp/config_<db>.json)
Secret-looking system parameters are reduced to "set"/"empty".
"""
import json

SECRET_WORDS = ("secret", "token", "key", "password", "passwd", "apikey", "api_key", "uuid", "code")


def plain(record, skip=()):
    out = {}
    for name, field in record._fields.items():
        if name in skip or not field.store or field.type in ("binary", "one2many") or name.startswith(("create_", "write_", "__")):
            continue
        if name in ("id", "display_name", "message_main_attachment_id"):
            continue
        value = record[name]
        if field.type == "many2one":
            value = value.display_name if value else False
        elif field.type == "many2many":
            value = sorted(value.mapped("display_name"))
        elif hasattr(value, "isoformat"):
            value = value.isoformat()
        out[name] = value
    return out


snap = {"db": env.cr.dbname}
snap["modules"] = sorted(env["ir.module.module"].search([("state", "=", "installed")]).mapped("name"))
snap["user_groups"] = sorted(env.ref("base.group_user").all_implied_ids.mapped("full_name")
                             if "all_implied_ids" in env["res.groups"]._fields
                             else env.ref("base.group_user").trans_implied_ids.mapped("full_name"))
params = {}
for p in env["ir.config_parameter"].sudo().search([]):
    secret = any(w in p.key.lower() for w in SECRET_WORDS)
    params[p.key] = ("set" if p.value else "empty") if secret else p.value
snap["params"] = params
snap["companies"] = {c.name: plain(c, skip=("logo", "logo_web", "favicon")) for c in env["res.company"].search([])}
snap["pos_configs"] = {c.name: plain(c) for c in env["pos.config"].with_context(active_test=False).search([])}
snap["payment_methods"] = {m.name: plain(m) for m in env["pos.payment.method"].with_context(active_test=False).search([])}
snap["warehouses"] = {w.code: plain(w) for w in env["stock.warehouse"].search([])}
snap["picking_types"] = {"%s/%s" % (t.warehouse_id.code, t.name): plain(t) for t in env["stock.picking.type"].search([])}
snap["pricelists"] = {p.name: {"items": [plain(i) for i in p.item_ids], **plain(p)} for p in env["product.pricelist"].search([])}
snap["fiscal_positions"] = sorted(env["account.fiscal.position"].search([]).mapped("name"))
snap["journals"] = sorted(env["account.journal"].search([]).mapped(lambda j: "%s (%s)" % (j.name, j.type)))
snap["routes"] = sorted(env["stock.route"].search([]).mapped("name")) if "stock.route" in env else []
snap["sequences_pos"] = {s.name: s.prefix for s in env["ir.sequence"].search([("code", "ilike", "pos")])}
if "grooming.price" in env:
    snap["grooming_prices"] = [plain(p) for p in env["grooming.price"].search([])]
if "grooming.service" in env:
    snap["grooming_services"] = [plain(s) for s in env["grooming.service"].search([])]

path = "/var/tmp/config_%s.json" % env.cr.dbname
with open(path, "w", encoding="utf-8") as f:
    json.dump(snap, f, ensure_ascii=False, indent=1, sort_keys=True, default=str)
env.cr.rollback()
print("SNAPSHOT", path)
