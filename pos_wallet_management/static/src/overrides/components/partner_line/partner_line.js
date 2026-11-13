/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { PartnerLine } from "@point_of_sale/app/screens/partner_list/partner_line/partner_line";
import { patch } from "@web/core/utils/patch";
import { useService } from "@web/core/utils/hooks";
import { WkErrorNotifyPopopWidget } from "@pos_wallet_management/app/popup/WkErrorNotifyPopopWidget";
import { CreateWalletPopopWidget } from "@pos_wallet_management/app/popup/CreateWalletPopopWidget";
import { WkWalletRechargePopup } from "@pos_wallet_management/app/popup/WkWalletRechargePopup";

patch(PartnerLine.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
        this.dialog = useService("dialog");
    },

    recharge_wallet() {
        var self = this;
        if (self.pos.wallet_method) {
            this.dialog.add(WkWalletRechargePopup, { 'partner': self.props.partner });
        }
        else {
            this.dialog.add(WkErrorNotifyPopopWidget, {
                title: _t('Sky Wallet payment method not found'),
                body: _t('Please configure the Sky Wallet payment method in Point of Sale settings.'),
            });
        }
    },

    create_wallet(ev) {
        var self = this;
        
        if (self.pos.wallet_method) {
            this.dialog.add(CreateWalletPopopWidget, {
                'partner': self.props.partner,
                'title': 'No Sky Wallet for selected customer',
                'body': 'You need to create a wallet for this customer before you can proceed to recharge'
            })
        }
        else {
            this.dialog.add(WkErrorNotifyPopopWidget, {
                title: _t('Sky Wallet payment method not found'),
                body: _t('Please configure the Sky Wallet payment method in Point of Sale settings.'),
            });
        }
    },
});
