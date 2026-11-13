/** @odoo-module */

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { Component } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { WkErrorNotifyPopopWidget } from "@pos_wallet_management/app/popup/WkErrorNotifyPopopWidget";
import { _t } from "@web/core/l10n/translation";
import { MainWalletRechargePopup } from "@pos_wallet_management/app/popup/MainWalletRechargePopup";

export class WalletRechargeWidget extends Component {
    static template = "pos_wallet_management.WalletRechargeWidget";
    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
    }
    async onClick() {
        if (this.pos.wallet_method) {
            this.dialog.add(MainWalletRechargePopup, {
                wallet_id: '',
            });
        }
        else {
            this.dialog.add(WkErrorNotifyPopopWidget, {
                title: _t('Sky Wallet payment method not found'),
                body: _t('Please configure the Sky Wallet payment method in Point of Sale settings.'),
            });
        }
    }
}
