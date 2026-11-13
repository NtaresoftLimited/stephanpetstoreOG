/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { formatDateTime } from "@web/core/l10n/dates";
import { parseUTCString } from "@point_of_sale/utils";
import { WkWalletRechargePopup } from "@pos_wallet_management/app/popup/WkWalletRechargePopup";
import { WkErrorNotifyPopopWidget } from "@pos_wallet_management/app/popup/WkErrorNotifyPopopWidget";

export class NFCScanWalletPopup extends Component {
    static components = { Dialog };
    static template = "pos_wallet_management.NFCScanWalletPopup";
    static props = [
        "close",
        "wallet",
        "getPayload?",
        "formatCurrency"
    ]
    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
    }

    getDate(item) {
        return formatDateTime(parseUTCString(item.create_date));
    }

    _callRechargeWallet(wallet_id){
        this.props.close();
        if (this.pos.wallet_method) {
            this.dialog.add(WkWalletRechargePopup,{
                'partner': this.props.wallet.partner_id,
            })
        }else{
            this.dialog.add(WkErrorNotifyPopopWidget, {
                title: _t('Sky Wallet payment method not found'),
                body: _t('Please configure the Sky Wallet payment method in Point of Sale settings.'),
            });
        }
    }

    selectCustomer(){
        const currentOrder = this.pos.get_order();
        if (!currentOrder) {
            return false;
        }
        currentOrder.set_partner(this.props.getPayload());
        this.props.close();
    }
}
