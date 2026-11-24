{
    'name': 'WhatsApp Connector (UltraMsg)',
    'version': '20.0.1.3.0',
    'category': 'Tools',
    'summary': 'Send WhatsApp messages and authenticate Portal customers via UltraMsg',
    'depends': ['base', 'mail', 'point_of_sale', 'web', 'portal'],
    'data': [
        'security/ir.access.csv',
        'views/whatsapp_instance_views.xml',
        'views/whatsapp_menus.xml',
        'views/pos_order_views.xml',
        'views/auth_whatsapp_templates.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'whatsapp_connector/static/src/css/portal_auth.css',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
