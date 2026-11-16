{
    "name": "Stephan's POS WhatsApp Receipts",
    "summary": "Send the POS receipt to the customer's WhatsApp from the Send Receipt popup",
    "version": "20.0.1.0.0",
    "category": "Sales/Point of Sale",
    "author": "Ntaresoft Limited",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "whatsapp_connector"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "stephans_pos_whatsapp/static/src/app/**/*",
        ],
    },
    "installable": True,
    "auto_install": False,
}
