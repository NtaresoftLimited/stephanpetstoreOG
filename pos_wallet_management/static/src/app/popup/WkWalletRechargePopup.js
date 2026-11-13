/** @odoo-module */

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { onMounted } from "@odoo/owl";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { _t } from "@web/core/l10n/translation";
import { WkErrorNotifyPopopWidget } from "@pos_wallet_management/app/popup/WkErrorNotifyPopopWidget";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class WkWalletRechargePopup extends Component {

    static template = "pos_wallet_management.WkWalletRechargePopup";
    static components = { Dialog };
    static defaultProps = {
        title: 'Confirm ?',
        body: '',
    };

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

    wk_validate_recharge() {
        var self = this;
        
        if (self.props && self.props.partner) {
            var recharge_amount = parseFloat($('.rechage_amount').val());
            var reason = $('.recharge_reason').val();
            if (recharge_amount <= 0 || !recharge_amount) {
                $('.rechage_amount').removeClass('text_shake');
                $('.rechage_amount').focus();
                $('.rechage_amount').addClass('text_shake');
                return;
            }
            else if (reason == "") {
                $('.recharge_reason').removeClass('text_shake');
                $('.recharge_reason').focus();
                $('.recharge_reason').addClass('text_shake');
                return;
            }
            else {
                var wallet_product = self.env.services.pos.wallet_product;

                if (wallet_product) {
                    var trans_data = {};
                    trans_data.amount = recharge_amount;
                    trans_data.trans_reason = reason;
                    trans_data.created_by = parseInt(self.env.services.pos.cashier ? self.env.services.pos.cashier.id : self.env.services.pos.user.id);
                    trans_data.partner_id = parseInt(self.props.partner.id);
                    if(self.props.partner.wallet_id[0]){
                        trans_data.wallet_id = parseInt(self.props.partner.wallet_id[0]);
                    }else{
                        trans_data.wallet_id = parseInt(self.props.partner.wallet_id.id);
                    }
                    trans_data.payment_type = 'CREDIT';
                    trans_data.wallet_product_id = wallet_product.id;
                    trans_data.state = 'confirm'
                    self.env.services.pos.add_new_order();
                    var curren_order = self.env.services.pos.get_order();
                    curren_order.wallet_recharge_data = trans_data;

                    self.env.services.pos.addLineToCurrentOrder({
                        product_id: wallet_product,
                        qty: 1,
                        price_unit: recharge_amount,
                    })

                    self.env.services.pos.showScreen("PaymentScreen", {
                        orderUuid: curren_order.uuid,
                    });
                    curren_order.get_selected_orderline().price_type = "manual";
                    curren_order.set_partner_for_wallet(self.props.partner, self.env.services.pos);
                    self.cancel()
                    self.env.services.pos.dialog.closeAll();
                }
                else {
                    this.dialog.add(WkErrorNotifyPopopWidget,{
                        title: _t('Sky Wallet recharge failed'),
                        body: _t('The Sky Wallet recharge product is not available in this POS.'),
                    })
                }
            }
        }
    }
    cancel(){
        this.props.close();
    }
}
