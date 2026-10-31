import gzip
import json
import traceback

INPUT = "/var/tmp/stephans_active_products.json.gz"


with gzip.open(INPUT, "rt", encoding="utf-8") as stream:
    payload = json.load(stream)


def existing_field_values(model, values):
    result = {}
    field_info = model.fields_get(list(values))
    for key, value in values.items():
        if key not in model._fields or model._fields[key].readonly:
            continue
        selection = field_info.get(key, {}).get("selection")
        if selection and value not in dict(selection):
            continue
        result[key] = value
    return result


def path_record(model_name, path):
    parent = env[model_name]
    for name in path:
        domain = [("name", "=", name)]
        if "parent_id" in env[model_name]._fields:
            domain.append(("parent_id", "=", parent.id or False))
        record = env[model_name].sudo().search(domain, limit=1)
        if not record:
            values = {"name": name}
            if "parent_id" in env[model_name]._fields:
                values["parent_id"] = parent.id or False
            record = env[model_name].sudo().create(values)
        parent = record
    return parent


def named_record(model_name, name, extra=None):
    if not name or model_name not in env:
        return env[model_name] if model_name in env else False
    record = env[model_name].sudo().search([("name", "=", name)], limit=1)
    if not record:
        values = {"name": name}
        values.update(extra or {})
        record = env[model_name].sudo().create(existing_field_values(env[model_name], values))
    return record


def tax_ids(items):
    ids = []
    for item in items:
        tax = env["account.tax"].sudo().search([
            ("name", "=", item["name"]), ("type_tax_use", "=", item["usage"]),
        ], limit=1)
        if tax:
            ids.append(tax.id)
    return ids


def find_template(item):
    xmlid = "stephans_product_migration.product_template_%s" % item["source_id"]
    module, xmlid_name = xmlid.split(".", 1)
    xmlid_record = env["ir.model.data"].sudo().search([
        ("module", "=", module), ("name", "=", xmlid_name), ("model", "=", "product.template"),
    ], limit=1)
    record = env["product.template"].sudo().with_context(active_test=False).browse(xmlid_record.res_id).exists() if xmlid_record else False
    if record and record.name == item["values"]["name"]:
        return record.with_context(Template.env.context), xmlid
    if xmlid_record:
        xmlid_record.unlink()

    claimed_ids = env["ir.model.data"].sudo().search([
        ("module", "=", "stephans_product_migration"), ("model", "=", "product.template"),
    ]).mapped("res_id")
    variants = item.get("variants", [])
    codes = [v["values"].get("default_code") for v in variants if v["values"].get("default_code")]
    barcodes = [v["values"].get("barcode") for v in variants if v["values"].get("barcode")]
    record = env["product.template"].sudo().with_context(active_test=False)
    if codes:
        match = env["product.product"].sudo().with_context(active_test=False).search([
            ("default_code", "in", codes), ("product_tmpl_id", "not in", claimed_ids),
            ("product_tmpl_id.name", "=", item["values"]["name"]),
        ], limit=1)
        if match:
            record = match.product_tmpl_id
    if not record and barcodes:
        match = env["product.product"].sudo().with_context(active_test=False).search([
            ("barcode", "in", barcodes), ("product_tmpl_id", "not in", claimed_ids),
            ("product_tmpl_id.name", "=", item["values"]["name"]),
        ], limit=1)
        if match:
            record = match.product_tmpl_id
    if not record:
        candidates = env["product.template"].sudo().with_context(active_test=False).search([
            ("name", "=", item["values"]["name"]), ("id", "not in", claimed_ids),
        ], limit=2)
        if len(candidates) == 1:
            record = candidates
    return record.with_context(Template.env.context) if record else record, xmlid


def register_xmlid(xmlid, record):
    module, name = xmlid.split(".", 1)
    data = env["ir.model.data"].sudo().search([("module", "=", module), ("name", "=", name)], limit=1)
    values = {"module": module, "name": name, "model": record._name, "res_id": record.id, "noupdate": True}
    data.write(values) if data else env["ir.model.data"].sudo().create(values)


created = updated = failed = images = 0
errors = []
Template = env["product.template"].sudo().with_context(
    active_test=False, tracking_disable=True, mail_create_nosubscribe=True, install_mode=True
)

for index, item in enumerate(payload["templates"], 1):
    try:
        template, xmlid = find_template(item)
        values = existing_field_values(Template, item["values"])
        source_type = item["values"].get("detailed_type") or item["values"].get("type") or "consu"
        values.pop("detailed_type", None)
        values.pop("type", None)
        if "type" in Template._fields:
            values["type"] = "service" if source_type == "service" else "consu"
        if "is_storable" in Template._fields:
            values["is_storable"] = source_type != "service"
        values["active"] = True
        values["image_1920"] = item.get("image_1920") or False
        if "approval_state" in Template._fields:
            values["approval_state"] = "approved"
        if item.get("category"):
            values["categ_id"] = path_record("product.category", item["category"]).id
        if item.get("uom"):
            uom = env["uom.uom"].sudo().search([("name", "=", item["uom"])], limit=1)
            if uom:
                values["uom_id"] = uom.id
        if item.get("purchase_uom") and "uom_po_id" in Template._fields:
            uom = env["uom.uom"].sudo().search([("name", "=", item["purchase_uom"])], limit=1)
            if uom:
                values["uom_po_id"] = uom.id
        values["taxes_id"] = [(6, 0, tax_ids(item.get("taxes", [])))]
        values["supplier_taxes_id"] = [(6, 0, tax_ids(item.get("supplier_taxes", [])))]
        values["public_categ_ids"] = [(6, 0, [path_record("product.public.category", p).id for p in item.get("website_categories", [])])]
        if "pos_categ_ids" in Template._fields:
            values["pos_categ_ids"] = [(6, 0, [path_record("pos.category", p).id for p in item.get("pos_categories", [])])]
        brand = named_record("product.brand", item.get("brand"))
        if brand:
            if "brand_id" in Template._fields:
                values["brand_id"] = brand.id
            if "product_brand_id" in Template._fields:
                values["product_brand_id"] = brand.id
        if "product_tag_ids" in Template._fields:
            values["product_tag_ids"] = [(6, 0, [named_record("product.tag", n).id for n in item.get("tags", [])])]

        if template:
            template.write(values); updated += 1
            template.attribute_line_ids.unlink()
        else:
            template = Template.create(values); created += 1
        register_xmlid(xmlid, template)

        line_commands = []
        for line in item.get("attribute_lines", []):
            attribute = named_record("product.attribute", line["attribute"], {
                "display_type": line.get("display_type") or "radio",
                "create_variant": line.get("create_variant") or "always",
            })
            value_ids = []
            for value in line["values"]:
                attribute_value = env["product.attribute.value"].sudo().search([
                    ("attribute_id", "=", attribute.id), ("name", "=", value["name"]),
                ], limit=1)
                if not attribute_value:
                    value_data = existing_field_values(env["product.attribute.value"], dict(value, attribute_id=attribute.id))
                    attribute_value = env["product.attribute.value"].sudo().create(value_data)
                value_ids.append(attribute_value.id)
            line_commands.append((0, 0, {"attribute_id": attribute.id, "value_ids": [(6, 0, value_ids)]}))
        if line_commands:
            template.write({"attribute_line_ids": line_commands})

        source_variants = {tuple(tuple(pair) for pair in variant["combination"]): variant for variant in item.get("variants", [])}
        for variant in template.product_variant_ids.with_context(active_test=False):
            combination = tuple(sorted((value.attribute_id.name, value.name) for value in variant.product_template_attribute_value_ids))
            source = source_variants.get(combination)
            if not source and len(source_variants) == 1 and not combination:
                source = next(iter(source_variants.values()))
            if not source:
                variant.active = False
                continue
            variant_values = existing_field_values(env["product.product"], source["values"])
            variant_values["active"] = True
            if source.get("image_variant_1920"):
                variant_values["image_variant_1920"] = source["image_variant_1920"]
            variant.write(variant_values)

        if item.get("gallery") and "product_template_image_ids" in template._fields:
            for gallery in item.get("gallery", []):
                image_values = existing_field_values(env["product.image"], dict(gallery, product_tmpl_id=template.id))
                env["product.image"].sudo().create(image_values); images += 1

        template.seller_ids.unlink()
        for supplier in item.get("suppliers", []):
            partner_data = supplier["partner"]
            domain = [("vat", "=", partner_data["vat"])] if partner_data.get("vat") else [("name", "=", partner_data["name"])]
            partner = env["res.partner"].sudo().search(domain, limit=1)
            if not partner:
                partner = env["res.partner"].sudo().create({k: v for k, v in partner_data.items() if v})
            supplier_values = dict(supplier)
            supplier_values.pop("partner")
            supplier_values.update({"partner_id": partner.id, "product_tmpl_id": template.id})
            if supplier_values.get("currency"):
                currency = env["res.currency"].sudo().search([("name", "=", supplier_values.pop("currency"))], limit=1)
                if currency:
                    supplier_values["currency_id"] = currency.id
            supplier_values = {k: v for k, v in supplier_values.items() if v not in ("", None)}
            env["product.supplierinfo"].sudo().create(existing_field_values(env["product.supplierinfo"], supplier_values))

        env.cr.commit()
        if index % 25 == 0:
            print("IMPORTED", index, "created", created, "updated", updated)
    except Exception as exc:
        env.cr.rollback(); failed += 1
        errors.append({"source_id": item["source_id"], "name": item["values"].get("name"), "error": str(exc)})
        print("FAILED", item["source_id"], item["values"].get("name"), str(exc))
        traceback.print_exc()

env.cr.commit()
with open("/var/tmp/stephans_product_import_errors.json", "w", encoding="utf-8") as stream:
    json.dump(errors, stream, indent=2)
print("IMPORT_COMPLETE", "source", len(payload["templates"]), "created", created, "updated", updated, "failed", failed, "gallery", images)
