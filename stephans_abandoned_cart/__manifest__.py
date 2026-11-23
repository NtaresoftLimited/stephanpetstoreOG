# -*- coding: utf-8 -*-
{
    "name": "Abandoned Cart Recovery",
    "version": "20.0.1.0.0",
    "category": "Website/eCommerce",
    "summary": "Recover lost sales automatically with quick reminder emails, templates & rich text editor",
    "description": """
Abandoned Cart Recovery for Odoo 20
===================================
Research shows about 60% to 80% of users who go to the checkout page do not complete their purchase.
Even the best optimized checkout process has an abandonment rate of 20%.

Features:
---------
* **Quick Reminder Emails:** Automatically detect abandoned carts and send reminder emails within minutes of inactivity.
* **Easy Template Setup:** Ready-to-use, beautiful abandoned cart email template with responsive product table and instant recovery link.
* **Powerful Rich Text Editor:** Fully compatible with Odoo's rich text editor and HTML styling—copy HTML from anywhere or customize visually.
* **Secure One-Click Cart Restoration:** Unique cryptographic recovery token restores the customer's exact cart session in one click.
* **Recovery Tracking & Analytics:** Real-time dashboard with pivot and graph views to track recovered revenue vs abandoned carts.
* **Send Test Emails:** Dedicated preview wizard to test emails with sample carts before live delivery.
""",
    "author": "Stephan's Pet Store",
    "website": "https://stephanspetstore.co.tz",
    "license": "LGPL-3",
    "depends": [
        "website_sale",
        "mail",
        "base_setup",
    ],
    "data": [
        "security/ir.access.csv",
        "data/mail_template.xml",
        "data/ir_cron.xml",
        "wizard/send_test_email_wizard_views.xml",
        "views/abandoned_cart_log_views.xml",
        "views/sale_order_views.xml",
        "views/res_config_settings_views.xml",
        "views/menu.xml",
    ],
    "installable": True,
    "application": True,
    "auto_install": False,
}
