# -*- coding: utf-8 -*-
{
    "name": "POS Receipt Design (Stephan's Design 3)",
    "version": "20.0.1.0.0",
    "category": "Point of Sale",
    "summary": "Stephan's Pet Store receipt layout (Design 3) for Odoo 20",
    "description": """
Odoo 20 port of the Odoo 18 custom_receipts_for_pos module as used by Stephan's Pet Store
(both tills on "Design 3").

Odoo 20 renders receipts from one QWeb template shared by the till and the server
(point_of_sale.pos_order_receipt), so Design 3 is an inherited template here instead of
receipt XML edited in the database and compiled inside the till. The till setting keeps the
Odoo 18 name (is_custom_receipt); logo, phone and email use Odoo 20's own receipt fields.
""",
    "author": "Cybrosys Techno Solutions; Odoo 20 port: Ntaresoft",
    "website": "https://www.cybrosys.com",
    "depends": ["point_of_sale"],
    "data": [
        "receipt/pos_order_receipt.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "custom_receipts_for_pos/static/src/generate_printer_data_patch.js",
        ],
    },
    "license": "AGPL-3",
    "installable": True,
}
