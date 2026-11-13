/** @odoo-module */

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { MainWalletRechargePopup } from "@pos_wallet_management/app/popup/MainWalletRechargePopup";
import { formatCurrency } from "@point_of_sale/app/models/utils/currency";
import { WkErrorNotifyPopopWidget } from "@pos_wallet_management/app/popup/WkErrorNotifyPopopWidget";
import { _t } from "@web/core/l10n/translation";
import { DataServiceOptions } from "@point_of_sale/app/models/data_service_options";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { WkWalletRechargePopup } from "@pos_wallet_management/app/popup/WkWalletRechargePopup";
import { OrderTabs } from "@point_of_sale/app/components/order_tabs/order_tabs";

patch(OrderTabs.prototype, {
    selectFloatingOrder(order) {
        super.selectFloatingOrder(order);
        if (order != null && order.wallet_recharge_data) {
            $('.rightpane').css("pointer-events", "none");
            $('.rightpane').css("opacity", "0.3");
        }
        else {
            $('.rightpane').css("pointer-events", "");
            $('.rightpane').css("opacity", "1");
        }
    },
});

patch(DataServiceOptions.prototype, {
    get databaseIndex(){
        return {
            ...super.databaseIndex,
            "pos.wallet": ["nfcid"],
        };
    }
})

patch(PosOrder.prototype, {
    setup() {
        super.setup(...arguments);
    },

    set_partner_for_wallet(partner, pos){
        var self = this;
        self.set_partner(partner);
        if (self) {
            if(self.check_existing_wallet_line(pos)!=null){
                self.remove_paymentline(self.check_existing_wallet_line(pos));
            }
        }
        return true;
    },

    set_partner(partner) {
        super.set_partner(partner);
    },

    check_existing_wallet_line(pos) {
        var self = this;
        var existing_wallet_line = null;
        var paymentlines = self.payment_ids;
        if(self && self.payment_ids && self.payment_ids.length){
            if (pos.wallet_method) {
                paymentlines.forEach(function (line) {
                    if (line.payment_method.id == pos.wallet_method.id) {
                        line.update({'is_wallet_payment_line': true});
                        existing_wallet_line = line;
                        return true;
                    }
                });
            }
        }
        return existing_wallet_line;
    },

    remove_paymentline(line) {
        super.remove_paymentline(line);
        var self = this;
        if (line && line.is_wallet_payment_line) {
            $('#use_wallet_payment').prop('checked', false);
            if (self.get_partner()){
                $('div.wallet_balance').html("Balance: <span style='color: #247b45;font-weight: bold;'>" + formatCurrency(self.get_partner().wallet_credits, this.currency) + "</span>");
            }

        }
    },

    wallet_remaining_balance() {
        var self = this;
        var paymentlines = self.get_paymentlines();
        var line_amount = 0;
        if (self.pos.wallet_journal) {
            paymentlines.forEach(function (line) {
                if (line.cashregister.journal.id == self.pos.wallet_journal.id) {
                    line_amount += line.amount;
                }
            });
        }
        var remianing_amount = self.get_partner().wallet_credits - line_amount
        return remianing_amount.toFixed(2)
    }
})


patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
    },

    async rechargeWallet(wallet_id) {
        if (this.wallet_method) {
            this.dialog.add(MainWalletRechargePopup, {
                wallet_id: wallet_id || '',
            });
        }
        else {
            this.dialog.add(WkErrorNotifyPopopWidget, {
                title: _t('Sky Wallet payment method not found'),
                body: _t('Please configure the Sky Wallet payment method in Point of Sale settings.'),
            });
        }
    },

    async processServerData() {
        await super.processServerData();
        this.wallets = this.data.models["pos.wallet"].getAll();
        this._loadJournalData();
        this._loadWalletsData();
        var products = this.data.models["product.product"].getAll();
        for (var i = 0, len = products.length; i < len; i++) {
            if (products[i].default_code == 'wk_wallet') {
                products[i].not_returnable = true;
                this.wallet_product = products[i];
            }
        }
    },
    _loadJournalData(){
        var self = this;
        var payment_methods = this.data.models['pos.payment.method'].getAll();
        payment_methods.forEach(function(journal){
            if(journal.wallet_method){
                self.wallet_method = journal
                return true;
            }
        })
    },
    _loadWalletsData(){
        var self = this;
        this.wallets = this.wallets.sort(function(a, b){
            return b.id - a.id;
        })
        self.all_wallets = self.wallets;
        self.wallet_by_name = {};
        self.wallets.forEach(function(wallet) {
            self.wallet_by_name[wallet.name] = wallet;
        })
    },
    async addLineToCurrentOrder(vals, opts = {}, configure = true) {
        var self = this;
        if (self.wallet_product && vals.product_id.id == self.wallet_product.id && !self.get_order().wallet_recharge_data) {
            this.dialog.add(MainWalletRechargePopup,{
                wallet_id: '',
            })
        }
        else{
            super.addLineToCurrentOrder(...arguments);
        }
    },

    async selectPartner(partner) {
        var current_order = this.get_order();
        if (current_order != null && current_order.wallet_recharge_data && this.is_wallet_orderline()) {
            
            this.dialog.add(AlertDialog,{
                title: _t("Customer Change Not Allowed!"),
                body: _t("Oops! You can't change the customer for a wallet recharge order.")
            })
        }
        else{
            const res = await super.selectPartner(partner);
            current_order.wallet_recharge_data = null;
            return res;
        }
    },

    is_wallet_orderline() {
        var self = this;
        var current_order = this.get_order();
        var wallet_line = false;
        if (current_order.get_orderlines() && self.wallet_product) {
            current_order.get_orderlines().forEach(function (orderline) {
                if (orderline.product_id.id == self.wallet_product.id)
                    wallet_line = true;
            });
        }
        return wallet_line;
    },

    openWalletRecharge(){
        if (this.wallet_method) {
            let order = this.get_order();
            if(order){
                let partner = order.get_partner();
                if(partner){
                    this.dialog.add(WkWalletRechargePopup,{
                        'partner': partner,
                    })
                }
            }
            
        }else{
            this.dialog.add(WkErrorNotifyPopopWidget, {
                title: _t('Sky Wallet payment method not found'),
                body: _t('Please configure the Sky Wallet payment method in Point of Sale settings.'),
            });
        }
    }
})
