# -*- coding: utf-8 -*-
{
    'name': 'Pet Grooming Services',
    'version': '20.0.1.0.5',
    'category': 'Services',
    'summary': 'Pet grooming appointment booking and management for Odoo 20',
    'description': """
        Complete pet grooming service management for Odoo 20.
        
        Features:
        - Service and pricing management
        - Add-on treatments
        - Appointment tracking
        - Customer portal appointments & pet management
        - Backend management views
    """,
    'author': 'Stephans Pet Store',
    'website': 'https://stephans-pet-store.com',
    'depends': [
        'base',
        'portal',
        'calendar',
        'mail',
        'sale_management',
        'account',
        'whatsapp_connector',
        'point_of_sale',
        'pos_sale',
        'pos_discount',
        'pos_loyalty',
        'stock',
        'product_auto_code',
    ],
    'data': [
        'security/ir.access.csv',
        'data/grooming_data.xml',
        'data/grooming_cron.xml',
        'data/grooming_prices.xml',
        'data/breed_data.xml',
        'data/portal_entry_data.xml',
        'views/grooming_views.xml',
        'views/expense_views.xml',
        'views/pet_views.xml',
        'views/grooming_dashboard.xml',
        'views/grooming_menus.xml',
        'views/portal_templates.xml',
        'views/stock_request_views.xml',
        'views/res_config_settings_views.xml',
        'views/stock_picking_views.xml',
        'views/account_payment_register_views.xml',
        'wizard/whatsapp_transfer_wizard_views.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'grooming/static/src/css/grooming_portal.css',
        ],
        'web.assets_backend': [
            'grooming/static/src/components/dashboard/grooming_dashboard.js',
            'grooming/static/src/components/dashboard/grooming_dashboard.xml',
            'grooming/static/src/components/dashboard/grooming_dashboard.css',
        ],
        'point_of_sale._assets_pos': [
            'grooming/static/src/xml/pos_actions.xml',
            'grooming/static/src/xml/request_stock_popup.xml',
            'grooming/static/src/xml/replenishment_request_popup.xml',
            'grooming/static/src/js/request_stock_popup.js',
            'grooming/static/src/js/replenishment_request_popup.js',
            'grooming/static/src/js/pos_control_buttons.js',
        ],
    },
    'license': 'LGPL-3',
    'installable': True,
    'application': True,
    'auto_install': False,
}
