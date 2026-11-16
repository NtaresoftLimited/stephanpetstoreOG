"""Export functional settings from Odoo 18 (read only) for sync_config_odoo20.py.

odoo-bin shell -c /etc/odoo/odoo_stephans.conf -d Stephans --no-http < export_config_odoo18.py
Writes /var/tmp/stephans_config.json. Employee PINs are included (needed for POS sign-in);
the file is created with mode 600.
"""
import json
import os

OUTPUT = "/var/tmp/stephans_config.json"
POS_CONFIGS = {5: "Stephan's Pet Store Masaki", 7: "Stephan's Pet Store Mikocheni"}
SKIP_POS_FIELDS = {
    "id", "name", "company_id", "currency_id", "journal_id", "invoice_journal_id", "sequence_id",
    "sequence_line_id", "uuid", "access_token", "current_session_id", "current_session_state",
    "last_session_closing_date", "last_session_closing_cash", "last_session_closing_cashbox",
    "picking_type_id", "warehouse_id", "payment_method_ids", "printer_ids", "proxy_ip",
    "epson_printer_ip", "in_stock_pick", "picking_type_location_id", "x_allowed_users",
}


def dt(value):
    return value.isoformat(sep=" ") if hasattr(value, "isoformat") else value


def hierarchy(record):
    names = []
    while record:
        names.append(record.name)
        record = record.parent_id
    return list(reversed(names))


def scalars(record, skip=()):
    out = {}
    for name, field in record._fields.items():
        if name in skip or not field.store or name.startswith(("create_", "write_")):
            continue
        if field.type in ("char", "text", "html", "boolean", "integer", "float", "monetary", "selection", "date", "datetime"):
            out[name] = dt(record[name])
    return out


def product_ref(product):
    return {"id": product.id, "template_id": product.product_tmpl_id.id, "default_code": product.default_code or False,
            "name": product.display_name,
            "combination": sorted([v.attribute_id.name, v.name] for v in product.product_template_attribute_value_ids),
            } if product else False


data = {"pos_configs": {}, "pricelists": [], "params": {}, "company": {}, "employees": [], "groups": {}}

for config_id, target in POS_CONFIGS.items():
    c = env["pos.config"].browse(config_id)
    data["pos_configs"][target] = {
        "scalars": scalars(c, SKIP_POS_FIELDS),
        "discount_product": product_ref(c.discount_product_id) if "discount_product_id" in c._fields else False,
        "tip_product": product_ref(c.tip_product_id),
        "pricelist": c.pricelist_id.name if c.pricelist_id else False,
        "available_pricelists": c.available_pricelist_ids.mapped("name"),
        "available_categories": [hierarchy(x) for x in c.iface_available_categ_ids],
        "basic_employees": c.basic_employee_ids.mapped("name") if "basic_employee_ids" in c._fields else [],
        "advanced_employees": c.advanced_employee_ids.mapped("name") if "advanced_employee_ids" in c._fields else [],
        "allowed_users": c.x_allowed_users.mapped("login") if "x_allowed_users" in c._fields else [],
        "warehouse": c.picking_type_id.warehouse_id.code,
        "picking_type_code": c.picking_type_id.code,
        "picking_type_name": c.picking_type_id.name,
    }

for pricelist in env["product.pricelist"].with_context(active_test=False).search([]):
    data["pricelists"].append({
        "name": pricelist.name, "active": pricelist.active, "currency": pricelist.currency_id.name,
        "sequence": pricelist.sequence,
        "items": [{
            "applied_on": item.applied_on, "compute_price": item.compute_price, "base": item.base,
            "fixed_price": item.fixed_price, "percent_price": item.percent_price,
            "price_discount": item.price_discount, "price_surcharge": item.price_surcharge,
            "price_round": item.price_round, "price_min_margin": item.price_min_margin,
            "price_max_margin": item.price_max_margin, "min_quantity": item.min_quantity,
            "date_start": dt(item.date_start), "date_end": dt(item.date_end),
            "product": product_ref(item.product_id),
            "template_id": item.product_tmpl_id.id or False,
            "template_name": item.product_tmpl_id.name or False,
            "category": hierarchy(item.categ_id) if item.categ_id else [],
            "base_pricelist": item.base_pricelist_id.name if item.base_pricelist_id else False,
        } for item in pricelist.item_ids],
    })

for p in env["ir.config_parameter"].sudo().search([("key", "=like", "stephans_pet_grooming.%")]):
    data["params"][p.key] = p.value

company = env["res.company"].browse(1)
data["company"] = {k: dt(company[k]) for k in (
    "report_footer", "report_header", "company_details", "primary_color", "secondary_color",
    "email_primary_color", "email_secondary_color", "tax_calculation_rounding_method",
    "point_of_sale_use_ticket_qr_code", "point_of_sale_ticket_portal_url_display_mode",
) if k in company._fields}
data["company"]["external_report_layout"] = company.external_report_layout_id.get_external_id().get(
    company.external_report_layout_id.id) if company.external_report_layout_id else False
data["company"]["layout_background"] = company.layout_background if "layout_background" in company._fields else False

for emp in env["hr.employee"].sudo().search([]):
    data["employees"].append({"name": emp.name, "pin": emp.pin or False, "barcode": emp.barcode or False,
                              "user_login": emp.user_id.login if emp.user_id else False,
                              "work_email": emp.work_email or False, "job_title": emp.job_title or False})

for xmlid in ("product.group_product_variant", "uom.group_uom", "stock.group_stock_multi_locations",
              "stock.group_stock_multi_warehouses", "product.group_product_pricelist",
              "stock.group_tracking_lot", "stock.group_production_lot", "account.group_cash_rounding"):
    group = env.ref(xmlid, raise_if_not_found=False)
    data["groups"][xmlid] = bool(group and group in env.ref("base.group_user").implied_ids)

with open(OUTPUT, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=1)
os.chmod(OUTPUT, 0o600)
env.cr.rollback()
print("EXPORT_COMPLETE", OUTPUT, "pricelists=%d items=%d employees=%d" % (
    len(data["pricelists"]), sum(len(p["items"]) for p in data["pricelists"]), len(data["employees"])))
print("GROUPS", data["groups"])
