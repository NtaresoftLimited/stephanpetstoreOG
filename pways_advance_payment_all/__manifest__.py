# -*- coding: utf-8 -*-
{
    'name' : "Sale Purchase Advance Payment",
    "author": "Preciseways",
    'category': 'Sales',
    'version': '18.0',
    'summary': """Advance payment for sale and purchase with auto adjustment of advance payment on invoice and bills confirmation
                sales advance payment
                sale advance payment
                purchase advance payment
                auto adjustment on invoice
                auto adjustment on payment
                auto invoice reconcilation
            auto bill reconcilation
                """,
    'description' : """Advance payment for sale and purchase with auto adjustment of advance payment in invoice and bills confirmation""",
    'depends' : ['sale_management','purchase','account'],
    'data': [
                'security/advance_payment_group.xml',
                'security/ir.model.access.csv',
                'wizard/sale_advance_payment_wizard.xml',
                'wizard/purchase_advance_payment_wizard.xml',
                'views/res_config_view.xml',
                'views/sale_order_view.xml',
                'views/purchase_order_view.xml',
             ],
    'installable': True,
    'auto_install': False,
    'price': 15,
    'currency': 'EUR',
    "license" : "OPL-1",
    "images":['static/description/banner.png'],
}
