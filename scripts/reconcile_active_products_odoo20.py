import collections
import gzip
import json


INPUT = "/var/tmp/stephans_active_products.json.gz"
MODULE = "stephans_product_migration"


def hierarchy(record):
    names = []
    while record:
        names.append(record.name)
        record = record.parent_id
    return list(reversed(names))


def normalized_variant(variant):
    return (
        variant.default_code or "",
        variant.barcode or "",
        round(variant.standard_price or 0.0, 6),
        round(variant.volume or 0.0, 6),
        round(variant.weight or 0.0, 6),
        tuple(sorted(
            (value.attribute_id.name, value.name)
            for value in variant.product_template_attribute_value_ids
        )),
    )


with gzip.open(INPUT, "rt", encoding="utf-8") as stream:
    payload = json.load(stream)

items = {item["source_id"]: item for item in payload["templates"]}
model_data = env["ir.model.data"].sudo().search([
    ("module", "=", MODULE),
    ("model", "=", "product.template"),
])
mappings = {}
for data in model_data:
    prefix = "product_template_"
    if not data.name.startswith(prefix):
        continue
    try:
        source_id = int(data.name[len(prefix):])
    except ValueError:
        continue
    if source_id in items:
        mappings[source_id] = data.res_id

results = collections.Counter()
details = collections.defaultdict(list)
results["source_templates"] = len(items)
results["mapping_rows"] = len(mappings)
results["unique_destination_templates"] = len(set(mappings.values()))

for source_id, item in items.items():
    destination_id = mappings.get(source_id)
    if not destination_id:
        details["missing_mapping"].append((source_id, item["values"].get("name")))
        continue
    template = env["product.template"].sudo().with_context(active_test=False).browse(destination_id).exists()
    if not template:
        details["missing_record"].append((source_id, destination_id))
        continue
    results["mapped_templates"] += 1
    results["active_mapped_templates"] += int(template.active)

    source_values = item["values"]
    if template.name != source_values.get("name"):
        details["name_mismatch"].append((source_id, source_values.get("name"), template.name))
    if abs(template.list_price - (source_values.get("list_price") or 0.0)) > 0.001:
        details["price_mismatch"].append((source_id, source_values.get("list_price"), template.list_price))
    source_published = bool(source_values.get("website_published") or source_values.get("is_published"))
    destination_published = bool(
        template.website_published if "website_published" in template._fields else template.is_published
    )
    if source_published != destination_published:
        details["publication_mismatch"].append((source_id, source_published, destination_published))
    if item.get("category") != hierarchy(template.categ_id):
        details["category_mismatch"].append((source_id, item.get("category"), hierarchy(template.categ_id)))
    destination_public_categories = sorted(hierarchy(category) for category in template.public_categ_ids)
    if sorted(item.get("website_categories", [])) != destination_public_categories:
        details["website_category_mismatch"].append(
            (source_id, item.get("website_categories", []), destination_public_categories)
        )

    source_has_image = bool(item.get("image_1920"))
    destination_has_image = bool(template.image_1920)
    results["source_templates_with_images"] += int(source_has_image)
    results["destination_templates_with_images"] += int(destination_has_image)
    if source_has_image != destination_has_image:
        details["image_presence_mismatch"].append((source_id, source_has_image, destination_has_image))

    source_variants = []
    for variant in item.get("variants", []):
        values = variant["values"]
        source_variants.append((
            values.get("default_code") or "",
            values.get("barcode") or "",
            round(values.get("standard_price") or 0.0, 6),
            round(values.get("volume") or 0.0, 6),
            round(values.get("weight") or 0.0, 6),
            tuple(tuple(pair) for pair in variant.get("combination", [])),
        ))
    destination_variants = [
        normalized_variant(variant)
        for variant in template.product_variant_ids.with_context(active_test=False).filtered("active")
    ]
    results["source_active_variants"] += len(source_variants)
    results["destination_active_variants"] += len(destination_variants)
    if collections.Counter(source_variants) != collections.Counter(destination_variants):
        details["variant_mismatch"].append((source_id, source_variants, destination_variants))

for key, values in sorted(details.items()):
    results[key] = len(values)

print("RECONCILIATION_RESULTS")
print(json.dumps(dict(sorted(results.items())), indent=2, sort_keys=True))
for key, values in sorted(details.items()):
    if values:
        print("DETAIL", key, json.dumps(values[:10], ensure_ascii=False, default=str))
print("RECONCILIATION_STATUS", "PASS" if not any(details.values()) else "FAIL")
