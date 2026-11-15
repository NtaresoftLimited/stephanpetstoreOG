"""Apply Odoo 18 functional settings to Odoo 20 (input: /var/tmp/stephans_config.json).

MIG_COMMIT=1 odoo-bin shell -c /etc/odoo/odoo20_stephans.conf -d stephans_odoo20 --no-http < sync_config_odoo20.py
Without MIG_COMMIT=1 it prints every change and rolls back.

Covers: POS till settings (fields that exist in both versions), PoS operation type, discount
product, cashier employees, pricelists, grooming settings, company report/receipt settings
and feature groups. Grooming prices are deliberately NOT copied (Odoo 20 holds the newer list).
"""
import json
import os

INPUT = "/var/tmp/stephans_config.json"
COMMIT = os.environ.get("MIG_COMMIT") == "1"
# Odoo 20 fields that must keep their Odoo 20 value even if Odoo 18 has a same-named field.
KEEP_POS_FIELDS = {"last_data_change", "order_seq_id", "order_line_seq_id", "device_seq_id",
                   "order_backend_seq_id", "active", "sequence", "module_pos_urban_piper",
                   # 70000 on Masaki is read by pos_dynamic_discount in Odoo 18; standard Odoo 20
                   # treats it as a percentage. Copy it only once that module is ported.
                   "discount_pc"}
SKIP_PARAMS = {"stephans_pet_grooming.mail_template_id"}  # record ids differ between databases

with open(INPUT, encoding="utf-8") as f:
    data = json.load(f)

changes = []


def note(label, field, old, new):
    changes.append("%s.%s: %r -> %r" % (label, field, str(old)[:60], str(new)[:60]))


def set_values(record, values, label):
    todo = {}
    for name, value in values.items():
        field = record._fields.get(name)
        if not field or field.readonly and not field.inverse:
            continue
        if field.type == "selection":
            selection = field._description_selection(record.env)
            if value not in dict(selection) and value is not False:
                continue
        current = record[name]
        if field.type == "many2one":
            current = current.id
        if field.type in ("datetime", "date") and current:
            current = current.isoformat(sep=" ") if field.type == "datetime" else current.isoformat()
        if (current or False) != (value or False):
            note(label, name, current, value)
            todo[name] = value
    if todo:
        record.write(todo)


def map_product(ref):
    if not ref:
        return env["product.product"]
    imd = env["ir.model.data"].sudo()
    rec = imd.search([("module", "=", "stephans_pos_migration"), ("name", "=", "product_product_%d" % ref["id"])], limit=1)
    if rec:
        return env["product.product"].browse(rec.res_id).exists()
    rec = imd.search([("module", "=", "stephans_product_migration"), ("name", "=", "product_template_%d" % ref["template_id"])], limit=1)
    tmpl = env["product.template"].with_context(active_test=False).browse(rec.res_id).exists() if rec else env["product.template"]
    if tmpl and len(tmpl.product_variant_ids) == 1:
        return tmpl.product_variant_ids
    if ref.get("default_code"):
        found = env["product.product"].with_context(active_test=False).search([("default_code", "=", ref["default_code"])])
        if len(found) == 1:
            return found
    return env["product.product"]


def map_template(template_id, name):
    rec = env["ir.model.data"].sudo().search([("module", "=", "stephans_product_migration"),
                                              ("name", "=", "product_template_%d" % template_id)], limit=1)
    tmpl = env["product.template"].with_context(active_test=False).browse(rec.res_id).exists() if rec else env["product.template"]
    if not tmpl and name:
        found = env["product.template"].with_context(active_test=False).search([("name", "=", name)])
        tmpl = found if len(found) == 1 else env["product.template"]
    return tmpl


# --- feature groups -------------------------------------------------------------------------
settings_vals = {}
setting_fields = env["res.config.settings"]._fields
for xmlid, enabled in data["groups"].items():
    field = next((n for n, f in setting_fields.items() if getattr(f, "implied_group", None) == xmlid), None)
    group = env.ref(xmlid, raise_if_not_found=False)
    if not field or not group:
        continue
    current = group in env.ref("base.group_user").all_implied_ids
    if current != enabled:
        note("feature", xmlid, current, enabled)
        settings_vals[field] = enabled
if settings_vals:
    env["res.config.settings"].create(settings_vals).execute()

# --- company ----------------------------------------------------------------------------------
company = env["res.company"].browse(1)
company_vals = {k: v for k, v in data["company"].items() if k not in ("external_report_layout",)}
set_values(company, company_vals, "company")
if data["company"].get("external_report_layout"):
    layout = env.ref(data["company"]["external_report_layout"], raise_if_not_found=False)
    if layout and company.external_report_layout_id != layout:
        note("company", "external_report_layout_id", company.external_report_layout_id.name, layout.name)
        company.external_report_layout_id = layout

# --- grooming settings ----------------------------------------------------------------------
params = env["ir.config_parameter"].sudo()
for key, value in data["params"].items():
    if key in SKIP_PARAMS:
        continue
    if params.get_str(key) != (value or ""):
        note("param", key, params.get_str(key), value)
        params.set_str(key, value or "")

# --- employees ----------------------------------------------------------------------------
Employee = env["hr.employee"].sudo().with_context(active_test=False)
employees = {}
for emp in data["employees"]:
    record = Employee.search([("name", "=", emp["name"])], limit=1)
    user = env["res.users"].with_context(active_test=False).search([("login", "=", emp["user_login"])], limit=1) if emp["user_login"] else env["res.users"]
    vals = {"name": emp["name"], "pin": emp["pin"] or False, "barcode": emp["barcode"] or False,
            "work_email": emp["work_email"], "job_title": emp["job_title"]}
    if user and not Employee.search([("user_id", "=", user.id), ("id", "!=", record.id)]):
        vals["user_id"] = user.id
    if not record:
        record = Employee.create(vals)
        changes.append("employee created: %s (pin %s)" % (emp["name"], "set" if emp["pin"] else "none"))
    else:
        safe = {k: v for k, v in vals.items() if k != "pin"}
        set_values(record, safe, "employee " + emp["name"])
        if (record.pin or False) != (emp["pin"] or False):
            record.pin = emp["pin"] or False
            changes.append("employee %s: pin updated" % emp["name"])
    employees[emp["name"]] = record

# --- pricelists -----------------------------------------------------------------------------
Pricelist = env["product.pricelist"].with_context(active_test=False)
for src in data["pricelists"]:
    pricelist = Pricelist.search([("name", "=", src["name"])], limit=1)
    if not pricelist:
        pricelist = Pricelist.create({"name": src["name"], "sequence": src["sequence"],
                                      "currency_id": env.ref("base.%s" % src["currency"]).id})
        changes.append("pricelist created: %s" % src["name"])
    pricelist.active = src["active"]
    item_cmds, missing = [(5, 0, 0)], 0
    for item in src["items"]:
        vals = {k: item[k] for k in ("applied_on", "compute_price", "base", "fixed_price", "percent_price",
                                    "price_discount", "price_surcharge", "price_round", "price_min_margin",
                                    "price_max_margin", "min_quantity", "date_start", "date_end")
                if k in env["product.pricelist.item"]._fields}
        if item["compute_price"] == "percentage":  # Odoo 20: percentage became "discount"
            vals["compute_price"] = "discount"
            vals["price_discount"] = item["percent_price"]
        elif item["compute_price"] == "formula":
            vals["compute_price"] = "discount" if not item["price_surcharge"] else "markup"
        if item["applied_on"] == "0_product_variant":
            product = map_product(item["product"])
            if not product:
                missing += 1
                continue
            vals["product_id"] = product.id
            vals["product_tmpl_id"] = product.product_tmpl_id.id
        elif item["applied_on"] == "1_product":
            tmpl = map_template(item["template_id"], item["template_name"])
            if not tmpl:
                missing += 1
                continue
            vals["product_tmpl_id"] = tmpl.id
        elif item["applied_on"] == "2_product_category" and item["category"]:
            categ = env["product.category"]
            for name in item["category"]:
                categ = env["product.category"].search([("name", "=", name), ("parent_id", "=", categ.id or False)], limit=1)
            if not categ:
                missing += 1
                continue
            vals["categ_id"] = categ.id
        if item["base_pricelist"]:
            base = Pricelist.search([("name", "=", item["base_pricelist"])], limit=1)
            vals["base_pricelist_id"] = base.id or False
        item_cmds.append((0, 0, vals))
    pricelist.write({"item_ids": item_cmds})
    changes.append("pricelist %s: %d rules set (%d not mapped)" % (src["name"], len(item_cmds) - 1, missing))

# --- POS tills --------------------------------------------------------------------------------
for name, src in data["pos_configs"].items():
    config = env["pos.config"].search([("name", "=", name)], limit=1)
    if not config:
        changes.append("MISSING till %s" % name)
        continue
    if config.current_session_id:
        raise SystemExit("Close the open session on %s first." % name)
    scalars = {k: v for k, v in src["scalars"].items() if k not in KEEP_POS_FIELDS}
    set_values(config, scalars, name)
    warehouse = env["stock.warehouse"].search([("code", "=", src["warehouse"])], limit=1)
    if warehouse.pos_type_id and config.picking_type_id != warehouse.pos_type_id:
        note(name, "picking_type_id", config.picking_type_id.display_name, warehouse.pos_type_id.display_name)
        config.picking_type_id = warehouse.pos_type_id
    if "discount_product_id" in config._fields:
        product = map_product(src["discount_product"])
        if product != config.discount_product_id:
            note(name, "discount_product_id", config.discount_product_id.display_name, product.display_name)
            config.discount_product_id = product.id or False
    tip = map_product(src["tip_product"])
    if tip != config.tip_product_id and not config.iface_tipproduct:
        note(name, "tip_product_id", config.tip_product_id.display_name, tip.display_name)
        config.tip_product_id = tip.id or False
    if "basic_employee_ids" in config._fields:
        basic = Employee.browse([employees[n].id for n in src["basic_employees"] if n in employees])
        advanced = Employee.browse([employees[n].id for n in src["advanced_employees"] if n in employees])
        if set(config.basic_employee_ids.ids) != set(basic.ids) or set(config.advanced_employee_ids.ids) != set(advanced.ids):
            note(name, "employees", config.basic_employee_ids.mapped("name"), basic.mapped("name"))
            config.write({"basic_employee_ids": [(6, 0, basic.ids)], "advanced_employee_ids": [(6, 0, advanced.ids)]})

for line in changes:
    print("CHANGE", line)
print("CHANGES", len(changes))
if COMMIT:
    env.cr.commit()
    print("COMMITTED")
else:
    env.cr.rollback()
    print("DRY RUN - rolled back")
