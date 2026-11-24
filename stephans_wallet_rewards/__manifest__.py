# -*- coding: utf-8 -*-
{
    "name": "Stephan's Sky Wallet & Paw Points",
    "summary": "Sky Wallet on the website (My Account + checkout) and native Paw Points loyalty for POS and eCommerce.",
    "description": """
Sky Wallet stays the single balance shared by the Point of Sale and the website:

* My Account (/my/wallet): balance, Paw Points and full wallet history.
* Website checkout: "Sky Wallet" payment option for signed-in customers with enough balance.
  Payments are debited from the same Sky Wallet ledger the POS uses.
* Paw Points: native Odoo loyalty program, 1 point per 1,000 TSh spent in store or online,
  100 points = 5,000 TSh off (5% back). Sky Wallet top-ups do not earn points (points are
  earned when spent).
* Paw Points are only earned/redeemed by customers with an active portal account (enforced
  server-side for website orders and POS orders; guests see "Log in to earn points").
""",
    "category": "Point of Sale",
    "version": "20.0.1.1.1",
    "author": "Ntaresoft Limited",
    "license": "LGPL-3",
    "depends": [
        "pos_wallet_management",
        "payment",
        "account_payment",
        "website_sale",
        "website_sale_loyalty",
        "pos_loyalty",
        "portal",
        "whatsapp_connector",  # shared portal styling (o_stephans_portal_*) and customer login
    ],
    "data": [
        "data/payment_provider_data.xml",
        "data/loyalty_data.xml",
        "data/portal_entry_data.xml",
        "views/payment_templates.xml",
        "views/portal_templates.xml",
        "views/pos_wallet_views.xml",
        "views/website_sale_templates.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "stephans_wallet_rewards/static/src/css/wallet_portal.css",
        ],
        "point_of_sale._assets_pos": [
            "stephans_wallet_rewards/static/src/pos/**/*",
        ],
    },
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "application": False,
}
