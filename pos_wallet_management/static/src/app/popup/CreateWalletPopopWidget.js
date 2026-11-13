/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { onMounted } from "@odoo/owl";
import { WkWalletRechargePopup } from "@pos_wallet_management/app/popup/WkWalletRechargePopup";
import { WkErrorNotifyPopopWidget } from "@pos_wallet_management/app/popup/WkErrorNotifyPopopWidget";
import { _t } from "@web/core/l10n/translation";
import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class CreateWalletPopopWidget extends Component {

    static template = "pos_wallet_management.CreateWalletPopopWidget";
    static components = { Dialog };
    static defaultProps = {
        title: 'Confirm ?',
        body: '',
    };

    setup() {
        super.setup();
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
        var self = this;
        if (self.props && self.props.partner) {
            
            var partner = self.props.partner;
            $('.button.create_wallet').css({ 'pointer-events': 'none' })
            try {
                const result = await this.env.services.orm.silent.call(
                    'pos.wallet',
                    'create_wallet_by_rpc',
                    [{ 'partner_id': parseInt(partner.id) }]
                );
                
                partner.wallet_id = [result.id, result.name];
                var wallet_details = result;
                wallet_details['partner_id'] = [partner.id, partner.name];
                wallet_details['partner'] = self.props.partner;
                
                if ($('.Partner-line.highlight .wallet_credits').length){
                    $('.Partner-line.highlight .wallet_credits').text(this.env.utils.formatCurrency(0));
                }
                else {
                    let Partner_line = $($('.partner-line')[$('.partner-line').length - 1]);
                    let data_id = Partner_line.data('id');
                    let partner = self.env.services.pos.models["res.partner"].getBy("id", data_id);                  
                    if (partner && partner.wallet_id) {
                        Partner_line.click();
                        Partner_line.children('.wallet_credits').text(this.env.utils.formatCurrency(partner.wallet_credits));
                    }
                }

                self.env.services.pos.wallet_by_name[result.name] = wallet_details;
                self.env.services.pos.all_wallets.push(wallet_details);
                $('.wk_confirm_mark').hide();
                $('.wallet_status').css({ 'display': 'inline-block' });
                $('#order_sent_status').hide();
                $('.wallet_status').removeClass('order_done');
                $('.show_tick').hide();
                setTimeout(function () {
                    $('.wallet_status').addClass('order_done');
                    $('.show_tick').show();
                    $('#order_sent_status').show();
                    $('.wallet_status').css({ 'border-color': '#5cb85c' });
                    $('.wk-alert center h2').text("Sky Wallet created");

                }, 500)
                setTimeout(function () {
                    self.cancel()
                    self.env.services.pos.dialog.add(WkWalletRechargePopup,
                        {
                            'partner':partner
                        }
                    )
                }, 1000);
                $('.recharge_wallet').show();
                $('.create_wallet').hide();
            } catch(error) {
                self.env.services.pos.dialog.add(WkErrorNotifyPopopWidget,
                    {
                        title: _t('Failed To create wallet'),
                        body: _t('Please make sure you are connected to the network.'),
                    }
                );
            }
        }
    }

    cancel(){
        this.props.close();
    }
}
