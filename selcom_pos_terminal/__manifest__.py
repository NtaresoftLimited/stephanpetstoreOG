{
    'name': 'Selcom Pos Terminal',
    'version': '20.0.1.0.0',
    'description': '',
    'summary': 'Connect your pos with selcom terminal',
    'author': 'TechKhedut Inc.',
    'maintainer': 'TechKhedut Inc.',
    'license': 'LGPL-3',
    'category': 'Point of Sale',
    'depends': [
        'point_of_sale',
    ],
    'data': [
        'views/selcom_pos_terminal_views.xml',
        'views/selcom_pos_terminal_payments_views.xml',
        'views/pos_payment_method_views.xml',

    ],
    # The Odoo 18 terminal JavaScript uses APIs removed in Odoo 20. Keep the
    # safe manual Selcom method available without loading a broken POS bundle;
    # terminal assets will be enabled after the Odoo 20 checkout flow is tested.
    'assets': {},
    'external_dependencies': {
        'python': ['selcom_apigw_client']
    },
    'images': [
        'static/src/img/selcom-logo.png',
    ],
    'installable': True,
}
