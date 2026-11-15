# -*- coding: utf-8 -*-
from odoo import api, models


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def wise_get_pos_stock(self, config_id, template_ids=None):
        """Stock per product for a POS till, counted at the till's own location.

        Returns {"products": {product_id: qty}, "templates": {template_id: qty}} for storable
        products sold in POS (template qty = sum of its variants). On-hand stock is summed from
        quants under the till location (child locations included), so it never falls back to the
        company-wide quantity.
        """
        config = self.env["pos.config"].browse(int(config_id))
        config.check_access("read")
        location = config._wise_stock_location()

        product_domain = [("is_storable", "=", True), ("available_in_pos", "=", True),
                          ("company_id", "in", [False, config.company_id.id])]
        if template_ids:
            product_domain.append(("product_tmpl_id", "in", [int(t) for t in template_ids]))
        products = self.env["product.product"].search(product_domain)

        if config.stock_type == "forecasted":
            ctx = {"location": location.id} if location else {}
            qty = {p.id: p.virtual_available for p in products.with_context(**ctx)}
        else:
            quant_domain = [("product_id", "in", products.ids), ("location_id.usage", "=", "internal"),
                            ("company_id", "=", config.company_id.id)]
            if location:
                quant_domain.append(("location_id", "child_of", location.id))
            groups = self.env["stock.quant"].sudo()._read_group(quant_domain, ["product_id"], ["quantity:sum"])
            qty = {product.id: total for product, total in groups}

        result = {"products": {}, "templates": {}}
        for product in products:
            value = qty.get(product.id, 0.0)
            result["products"][product.id] = value
            tmpl_id = product.product_tmpl_id.id
            result["templates"][tmpl_id] = result["templates"].get(tmpl_id, 0.0) + value
        return result
