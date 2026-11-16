/** @odoo-module */

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { onMounted, useProps } from "@odoo/owl";
import { WkWalletRechargePopup } from "@pos_wallet_management/app/popup/WkWalletRechargePopup";
import { WkErrorNotifyPopopWidget } from "@pos_wallet_management/app/popup/WkErrorNotifyPopopWidget";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";

export class CreateWalletPopopWidget extends Component {

    static template = "pos_wallet_management.CreateWalletPopopWidget";
    static components = { Dialog };
    // Odoo 20 / OWL 3: components only get this.props through useProps().
    props = useProps();

    setup() {
        super.setup();
        this.pos = usePos();
        onMounted(this.mounted);
    }

    mounted() {
        var self = this;
        setTimeout(function () {
            $('.move').addClass('complete');
        }, 500)
        $('.create_wallet').css({ 'pointer-events': 'all' });
    }

    async click_create_wallet() {
        // Odoo 20 port: create through the POS data service, then re-read the customer and wallet
        // so partner.wallet_id / wallet_credits are real records instead of hand-built arrays.
        const pos = this.pos;
        const partner = this.props?.partner;
        if (!partner || this.creating) {
            return;
        }
        this.creating = true;
        try {
            const result = await pos.data.call("pos.wallet", "create_wallet_by_rpc", [{ partner_id: partner.id }]);
            await pos.data.read("pos.wallet", [result.id]);
            await pos.refreshWalletPartner(partner);
            $('.wk_confirm_mark').hide();
            $('.wallet_status').css({ 'display': 'inline-block' });
            $('.show_tick').hide();
            setTimeout(() => {
                $('.wallet_status').addClass('order_done');
                $('.show_tick').show();
                $('.wallet_status').css({ 'border-color': '#5cb85c' });
                $('.wk-alert center h2').text(_t("Sky Wallet created"));
            }, 500);
            setTimeout(() => {
                this.cancel();
                pos.dialog.add(WkWalletRechargePopup, { partner });
            }, 1000);
        } catch (error) {
            this.creating = false;
            pos.dialog.add(WkErrorNotifyPopopWidget, {
                title: _t('Failed To create wallet'),
                body: _t('Please make sure you are connected to the network.'),
            });
        }
    }

    cancel(){
        this.props.close();
    }
}
