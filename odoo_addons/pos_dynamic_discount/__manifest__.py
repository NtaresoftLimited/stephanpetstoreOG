# -*- coding: utf-8 -*-
{
    "name": "POS Dynamic Discount in Amount and Percentage",
    "summary": """POS Global discount, POS dynamic discount, POS Global discount Amount and Percentage, Point Of Sale Discount, apply POS discount base on amount, apply pos discount base on percentage,POS Discount Amount Display, discount pos global, dynamic pos discount, pos dynamic,POS Global Discount point of sales fixed POS global Discount on POS pos discount pos retail """,
    "description": """POS Global Dynamic Discount in Amount and Percentage""",
    "category": "Point of Sale",
    'author': 'Khaled Hassan',
    'website': "https://apps.odoo.com/apps/modules/browse?search=Khaled+hassan",
    "version": "18.0.1.0.0",
    'price': 25,
    'currency': 'EUR',
    "depends": ["pos_discount"],
    'license': 'OPL-1',
    "installable": True,
    "auto_install": False,
    'data': [
        'views/pos_config_views.xml',
    ],
    'assets': {
        'point_of_sale._assets_pos': [
            'pos_dynamic_discount/static/src/css/**/*.css',
            'pos_dynamic_discount/static/src/js/orderline_patch.js',
            'pos_dynamic_discount/static/src/js/dynamic_discount.js',
            'pos_dynamic_discount/static/src/js/discount_display.js',
            'pos_dynamic_discount/static/src/xml/**/*.xml',
        ],
    },
    'images': ['static/description/main_screenshot.png'],
}