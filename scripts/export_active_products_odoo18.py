import gzip
import json

OUTPUT = "/var/tmp/stephans_active_products.json.gz"


def binary(value):
    return value.decode("ascii") if isinstance(value, bytes) else (value or False)


def hierarchy(record):
    names = []
    while record:
        names.append(record.name)
        record = record.parent_id
    return list(reversed(names))


def scalar_values(record, names):
    values = {}
    for name in names:
        if name not in record._fields:
            continue
        field = record._fields[name]
        if field.type not in ("char", "text", "html", "boolean", "integer", "float", "selection", "date", "datetime"):
            continue
        value = record[name]
        values[name] = value.isoformat() if hasattr(value, "isoformat") else value
    return values


template_fields = [
    "name", "sequence", "description", "description_sale", "description_purchase",
    "type", "detailed_type", "sale_ok", "purchase_ok", "list_price", "standard_price",
    "volume", "weight", "sale_delay", "tracking", "invoice_policy", "purchase_method",
    "expense_policy", "available_in_pos", "to_weight", "can_be_expensed", "active",
    "website_published", "is_published", "website_description", "description_ecommerce",
    "website_meta_title", "website_meta_description", "website_meta_keywords", "seo_name",
    "show_availability", "allow_out_of_stock_order", "out_of_stock_message", "service_type",
    "service_tracking", "purchase_line_warn", "purchase_line_warn_msg", "sale_line_warn",
    "sale_line_warn_msg", "hs_code",
]
variant_fields = ["default_code", "barcode", "standard_price", "volume", "weight", "active"]

templates = env["product.template"].sudo().with_context(active_test=False).search(
    [("active", "=", True)], order="id"
)
payload = {"source_database": env.cr.dbname, "templates": []}

for index, template in enumerate(templates, 1):
    item = {
        "source_id": template.id,
        "values": scalar_values(template, template_fields),
        "image_1920": binary(template.image_1920),
        "category": hierarchy(template.categ_id) if template.categ_id else [],
        "uom": template.uom_id.name if template.uom_id else False,
        "purchase_uom": template.uom_po_id.name if template.uom_po_id else False,
        "taxes": [{"name": tax.name, "usage": tax.type_tax_use, "amount": tax.amount} for tax in template.taxes_id],
        "supplier_taxes": [{"name": tax.name, "usage": tax.type_tax_use, "amount": tax.amount} for tax in template.supplier_taxes_id],
        "website_categories": [hierarchy(category) for category in template.public_categ_ids],
        "pos_categories": [hierarchy(category) for category in template.pos_categ_ids] if "pos_categ_ids" in template._fields else [],
        "brand": template.brand_id.name if "brand_id" in template._fields and template.brand_id else False,
        "tags": template.product_tag_ids.mapped("name") if "product_tag_ids" in template._fields else [],
        "attribute_lines": [],
        "variants": [],
        "gallery": [],
        "suppliers": [],
    }
    for line in template.attribute_line_ids:
        item["attribute_lines"].append({
            "attribute": line.attribute_id.name,
            "display_type": line.attribute_id.display_type,
            "create_variant": line.attribute_id.create_variant,
            "values": [{
                "name": value.name,
                "sequence": value.sequence,
                "html_color": value.html_color if "html_color" in value._fields else False,
                "is_custom": value.is_custom if "is_custom" in value._fields else False,
            } for value in line.value_ids],
        })
    for variant in template.product_variant_ids.with_context(active_test=False).filtered("active"):
        item["variants"].append({
            "source_id": variant.id,
            "values": scalar_values(variant, variant_fields),
            "image_variant_1920": binary(variant.image_variant_1920),
            "combination": sorted([(v.attribute_id.name, v.name) for v in variant.product_template_attribute_value_ids]),
        })
    if "product_template_image_ids" in template._fields:
        for image in template.product_template_image_ids:
            item["gallery"].append({
                "name": image.name, "sequence": image.sequence,
                "image_1920": binary(image.image_1920),
                "video_url": image.video_url if "video_url" in image._fields else False,
            })
    for supplier in template.seller_ids:
        item["suppliers"].append({
            "partner": {"name": supplier.partner_id.name, "email": supplier.partner_id.email, "vat": supplier.partner_id.vat},
            "min_qty": supplier.min_qty, "price": supplier.price, "delay": supplier.delay,
            "currency": supplier.currency_id.name if supplier.currency_id else False,
            "product_name": supplier.product_name, "product_code": supplier.product_code,
            "date_start": str(supplier.date_start or ""), "date_end": str(supplier.date_end or ""),
        })
    payload["templates"].append(item)
    if index % 100 == 0:
        print("EXPORTED", index)

with gzip.open(OUTPUT, "wt", encoding="utf-8") as stream:
    json.dump(payload, stream, ensure_ascii=False)
print("EXPORT_COMPLETE", OUTPUT, len(payload["templates"]))
