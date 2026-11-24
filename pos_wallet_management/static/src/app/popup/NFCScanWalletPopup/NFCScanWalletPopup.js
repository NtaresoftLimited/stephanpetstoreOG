/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { Component, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { useService } from "@web/core/utils/hooks";
import { formatDateTime, deserializeDateTime } from "@web/core/l10n/dates";
import { WkWalletRechargePopup } from "@pos_wallet_management/app/popup/WkWalletRechargePopup";
import { WkErrorNotifyPopopWidget } from "@pos_wallet_management/app/popup/WkErrorNotifyPopopWidget";

export class NFCScanWalletPopup extends Component {
    static components = { Dialog };
    // Odoo 20 / OWL 3: components only get this.props through useProps().
    props = useProps();
    static template = "pos_wallet_management.NFCScanWalletPopup";
    setup() {
        this.pos = usePos();
        this.dialog = useService("dialog");
    }

    getDate(item) {
        // Odoo 20 models may already hold a luxon DateTime.
        const value = item.create_date;
        if (!value) {
            return "";
        }
        return formatDateTime(typeof value === "string" ? deserializeDateTime(value) : value);
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
        const currentOrder = this.pos.getOrder();
        if (!currentOrder) {
            return false;
        }
        currentOrder.setPartner(this.props.getPayload());
        this.props.close();
    }
}
