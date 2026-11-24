# -*- coding: utf-8 -*-
{
    "name": "POS Dynamic Discount Limits",
    "summary": "Per-till limits on the POS global discount (percentage and fixed amount)",
    "description": """
Odoo 20 port of the Odoo 18 pos_dynamic_discount module used by Stephan's Pet Store.

Odoo 20's own pos_discount button already offers both a percentage and a fixed-amount
discount, applied as an exact discount line with correct taxes and refunds. This port keeps
the Odoo 18 field names and values (max_percentage_discount, max_fixed_amount_discount) and
enforces them on that button, so the settings migrate unchanged.
""",
    "category": "Point of Sale",
    "author": "Khaled Hassan; Odoo 20 port: Ntaresoft",
    "version": "20.0.1.0.0",
    "depends": ["pos_discount"],
    "license": "OPL-1",
    "installable": True,
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_dynamic_discount/static/src/control_buttons_patch.js",
        ],
    },
}
