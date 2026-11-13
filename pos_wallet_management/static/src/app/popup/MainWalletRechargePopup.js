/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { WkWalletRechargePopup } from "@pos_wallet_management/app/popup/WkWalletRechargePopup";
import { Component, useRef, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class MainWalletRechargePopup extends Component {

    static template = "pos_wallet_management.MainWalletRechargePopup";
    static components = { Dialog };
    static defaultProps = {
        title: 'Confirm ?',
        body: '',
    };
    static props= ["wallet_id","close"]
    setup() {
        super.setup();
        onMounted(this.WOnMounted);
        this.dialog = useService("dialog");
    }

    WOnMounted() {
        var self = this;
        setTimeout(function () {
            $('.move').addClass('complete');
        }, 500);
        $('.wallet_input').focus();
        self.index = -1;
        self.parent = $('.wallet-holder');
    }

    wallet_key_press_input(event) {
        var self = this;
        var updown_press;
        var all_wallets = self.env.services.pos.all_wallets;
        $('.wallet-holder ul').empty();
        var search = $('.wallet_input').val();
        $('.wallet-holder').show();
        search = new RegExp(search.replace(/[^0-9a-z_]/i), 'i');
        for (var index in all_wallets) {
            if (all_wallets[index].name.match(search)) {
                if(all_wallets[index].state == 'confirm'){
                    $('.wallet-holder ul').append($("<li><span class='wallet-name'>" + all_wallets[index].name + "</span></li>"));
                }
            }
        }

        if ($('.wallet-holder')[0] && $('.wallet-holder')[0].style.display != "none")
            $('.wallet_details').hide();

        $('.wallet-holder ul').show();
        $('.wallet-holder li').on('click', function () {
            var quotation_id = $(this).text();
            $(".wallet_input").val(quotation_id);
            $('.wallet-holder').hide();
            $(".wallet_input").blur();
        });

        if (event.which == 38) {
            // Up arrow
            self.index--;
            var len = $('.wallet-holder li').length;
            if (self.index < 0)
                self.index = len - 1;
            updown_press = true;
        } else if (event.which == 40) {
            self.index++;
            if (self.index > $('.wallet-holder li').length - 1)
                self.index = 0;
            updown_press = true;
        }
        if (updown_press) {
            $('.wallet-holder li.active').removeClass('active');
            $('.wallet-holder li').eq(self.index).addClass('active');
            $('.wallet-holder li.active').select();
        }

        if (event.which == 27) {
            // Esc key
            $('.wallet-holder ul').hide();
        } else if (event.which == 13 && self.index >= 0 && $('.wallet-holder li').eq(self.index)[0]) {
            var selcted_li_wallet_id = $('.wallet-holder li').eq(self.index)[0].innerText;
            $(".wallet_input").val(selcted_li_wallet_id);
            $('.wallet-holder ul').hide();
            $('.wallet-holder').hide();
            self.index = -1;
            $('.wallet_input').focusout();

        }
    }
    click_validate_wallet() {
        var self = this;
        var wallet_input = $('.wallet_input').val();
        if (wallet_input && self.env.services.pos.wallet_by_name[wallet_input]) {
            var wallet = self.env.services.pos.wallet_by_name[wallet_input];
            if (wallet && wallet.partner_id) {
                self.cancel()
                this.dialog.add(WkWalletRechargePopup,{
                    'partner': wallet.partner_id
                })
            }
        }
        else {
            $('.wallet_input').addClass('text_shake')
            setTimeout(function () {
                $('.wallet_input').removeClass('text_shake');
            }, 500);
        }
    }

    cancel(){
        this.props.close();
    }
}

