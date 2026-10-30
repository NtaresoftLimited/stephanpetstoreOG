{
    'name': 'WhatsApp Connector (UltraMsg)',
    'version': '18.0.1.2.0',
    'category': 'Tools',
    'summary': 'Send WhatsApp messages and authenticate Portal customers via UltraMsg',
    'depends': ['base', 'mail', 'point_of_sale', 'web', 'portal'],
    'data': [
        'security/ir.model.access.csv',
        'views/whatsapp_instance_views.xml',
        'views/whatsapp_menus.xml',
        'views/pos_order_views.xml',
        'views/auth_whatsapp_templates.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
