# -*- coding: utf-8 -*-
#################################################################################
# Author      : Webkul Software Pvt. Ltd. (<https://webkul.com/>)
# Copyright(c): 2015-Present Webkul Software Pvt. Ltd.
# All Rights Reserved.
#
#
#
# This program is copyright property of the author mentioned above.
# You can`t redistribute it and/or modify it.
#
#
# You should have received a copy of the License along with this program.
# If not, see <https://store.webkul.com/license.html/>
#################################################################################
{
    "name":  "Sky Wallet",
    "summary":  """Shared Sky Wallet customer credit for Stephan's Point of Sale.""",
    "category":  "Point of Sale",
    "version":  "20.0.2.1.0",
    "sequence":  1,
    "author":  "Webkul Software Pvt. Ltd.",
    "license":  "Other proprietary",
    "website":  "https://store.webkul.com/Odoo-POS-Wallet-Management.html",
    "description":  """Sky Wallet provides shared customer credit, recharge,
                        payment, refund and transaction history in Point of Sale.""",
    "live_test_url":  "http://odoodemo.webkul.com/?module=pos_wallet_management&custom_url=/pos/auto",
    "depends":  [
        'point_of_sale',
        'sale',
    ],
    "data":  [
        'security/ir.access.csv',
        'wizard/pos_wallet_cancellation.xml',
        'views/pos_wallet_management_view.xml',
        'views/wallet_sequence_view.xml',
        'data/pos_wallet_data.xml'
    ],
    "demo":  [
                'data/demo_product.xml',
            ],
    "assets": {

        'point_of_sale._assets_pos':
        [
            'pos_wallet_management/static/lib/jquery/jquery.min.js',
            'pos_wallet_management/static/src/app/**/*',
            'pos_wallet_management/static/src/overrides/**/*',
            'pos_wallet_management/static/src/css/**/*',
        ],
    },
    "images":  ['static/description/Banner.png'],
    "application":  True,
    "installable":  True,
    "auto_install":  False,
    "price":  169,
    "currency":  "USD",
    "pre_init_hook":  "pre_init_check",
}
