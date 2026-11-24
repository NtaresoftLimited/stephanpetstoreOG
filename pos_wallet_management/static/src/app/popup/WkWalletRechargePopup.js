/** @odoo-module */

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { onMounted, useProps } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { _t } from "@web/core/l10n/translation";
import { WkErrorNotifyPopopWidget } from "@pos_wallet_management/app/popup/WkErrorNotifyPopopWidget";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class WkWalletRechargePopup extends Component {

    static template = "pos_wallet_management.WkWalletRechargePopup";
    static components = { Dialog };
    // Odoo 20 / OWL 3: components only get this.props through useProps().
    props = useProps();

    setup() {
        super.setup();
        this.pos = usePos();
        onMounted(this.OnMounted);
    }

    OnMounted() {
        var self = this;
        setTimeout(function () {
            $('.move').addClass('complete');
        }, 500)
        
        $('.rechage_amount').attr('placeholder', "Amount (" + this.pos.currency.symbol + ")")
        $('.rechage_amount').focus();
    }

    async wk_validate_recharge() {
        // Odoo 20 port: new order via addNewOrder, lines by product template, navigate() instead of
        // showScreen, and wallet_recharge_data stored as JSON text (the server json.loads it).
        const pos = this.pos;
        const partner = this.props?.partner;
        if (!partner) {
            return;
        }
        const recharge_amount = parseFloat($('.rechage_amount').val());
        const reason = $('.recharge_reason').val();
        if (!recharge_amount || recharge_amount <= 0) {
            $('.rechage_amount').removeClass('text_shake').focus().addClass('text_shake');
            return;
        }
        if (!reason) {
            $('.recharge_reason').removeClass('text_shake').focus().addClass('text_shake');
            return;
        }
        const wallet_product = pos.wallet_product;
        if (!wallet_product) {
            pos.dialog.add(WkErrorNotifyPopopWidget, {
                title: _t('Sky Wallet recharge failed'),
                body: _t('The Sky Wallet recharge product is not available in this POS.'),
            });
            return;
        }
        if (!partner.wallet_id) {
            pos.dialog.add(WkErrorNotifyPopopWidget, {
                title: _t('No Sky Wallet for selected customer'),
                body: _t('Create a Sky Wallet for this customer before recharging.'),
            });
            return;
        }
        const order = pos.addNewOrder();
        order.wallet_recharge_data = JSON.stringify({
            amount: recharge_amount,
            trans_reason: reason,
            created_by: pos.user?.id,
            partner_id: partner.id,
            wallet_id: partner.wallet_id.id,
            payment_type: 'CREDIT',
            wallet_product_id: wallet_product.id,
            state: 'confirm',
        });
        order.setPartner(partner);
        await pos.addLineToCurrentOrder(
            {
                product_tmpl_id: wallet_product.product_tmpl_id,
                product_id: wallet_product,
                qty: 1,
                price_unit: recharge_amount,
            },
            {},
            false
        );
        this.cancel();
        pos.dialog.closeAll();
        pos.navigate("PaymentScreen", { orderUuid: order.uuid });
    }

    cancel(){
        this.props.close();
    }
}
