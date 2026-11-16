# -*- coding: utf-8 -*-
# Original module (Odoo 18): Wisenetic Technologies. Odoo 20 port for Stephan's Pet Store.
{
    "name": "POS Stock",
    "summary": "Show till-location stock on POS product cards, hide or block out-of-stock products, "
               "low stock list and margin restriction.",
    "author": "Wisenetic, Ntaresoft",
    "website": "https://www.wisenetic.com",
    "category": "Sales/Point of Sale",
    "version": "20.0.1.0.0",
    "depends": ["point_of_sale", "pos_stock"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "wise_pos_stock/static/src/**/*",
        ],
    },
    "installable": True,
    "application": False,
    "license": "OPL-1",
}
