/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { ConfirmationDialog, AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

import {
    roundDecimals as round_di,
} from "@web/core/utils/numbers";
import { WkErrorNotifyPopopWidget } from "@pos_wallet_management/app/popup/WkErrorNotifyPopopWidget";
import { PosPayment } from "@point_of_sale/app/models/pos_payment";

patch(PosPayment,{
    extraFields: {
        ...(PosPayment.extraFields || {}),
        is_wallet_payment_line: {
            model: "pos.payment",
            name: "is_wallet_payment_line",
            type: "boolean",
            local: true,
        },
    },
});

patch(PaymentScreen.prototype, {
    setup() {
        super.setup();
        this.barcode = useService("barcode");
        this.barcode.bus.addEventListener("barcode_scanned", async (ev) => {
            if(ev.detail.barcode){
                const nfcid = ev.detail.barcode;
                let wallet = this.pos.models["pos.wallet"].getBy("nfcid", nfcid);
                if (!wallet) {
                    const ids = await this.pos.data.call("pos.wallet", "search", [[["nfcid", "=", nfcid]]], {});
                    if (ids.length) {
                        await this.pos.data.read("pos.wallet", [ids[0]]);
                        wallet = this.pos.models["pos.wallet"].getBy("id", ids[0]);
                    }
                }
                const currentOrder = this.pos.get_order();
                this.props.orderUuid = currentOrder.uuid;

                if(!wallet || !currentOrder || this.pos.mainScreen.component.name != 'PaymentScreen') return;

                setTimeout(()=>{
                    $('button.o_notification_close').click()
                },50)

                if(this.pos.is_wallet_orderline()){
                    this.dialog.add(AlertDialog,{
                        title: _t("Not Allowed !"),
                        body: _t("Sky Wallet recharge using an NFC card is not allowed.")
                    })
                    return;
                }
                currentOrder.set_partner(wallet.partner_id);
                await this.wkOnMounted();
                var paymentMethod = this.pos.wallet_method;
                await this.addNewPaymentLine(paymentMethod)
                if (this.check_existing_wallet_line())
                    $('#use_wallet_payment').prop('checked', true);
            } else {
                
            }    
        });
        onMounted(this.wkOnMounted);
    },

    check_existing_wallet_line() {
        var self = this;
        var current_order = self.pos.get_order();
        var existing_wallet_line = null;
        var paymentlines = current_order.payment_ids;
        if(paymentlines.length){
            if (self.pos.wallet_method) {
                paymentlines.forEach(function (line) {
                    if (line.payment_method_id.id == self.pos.wallet_method.id) {
                        line.update({'is_wallet_payment_line': true});
                        existing_wallet_line = line;
                    }
                });
            }
        }
        return existing_wallet_line;
    },
    
    async addNewPaymentLine(paymentMethod) {
        try {
            const current_order = this.pos.get_order();
            const partner = current_order.get_partner();
            let due = current_order.get_due();
            if (!paymentMethod.wallet_method) {
                return await super.addNewPaymentLine(...arguments);
            }
            // Case: No customer selected
            if (!partner) {
                return await this.dialog.add(ConfirmationDialog, {
                    body: _t("Select a customer before using Sky Wallet."),
                    confirmLabel: _t("Customers"),
                    confirm: async () => {
                        const currentPartner = this.currentOrder.get_partner();
                        const { confirmed, payload: newPartner } = await this.showTempScreen('PartnerListScreen', {
                            Partner: currentPartner
                        });
                        if (confirmed) {
                            this.currentOrder.set_partner_for_wallet(newPartner, this.pos);
                            this.currentOrder.updatePricelist(newPartner);
                        }
                    },
                    cancel: () => {},
                });
            }

            // Case: Wallet not configured for customer
            if (!partner.wallet_id) {
                return this.dialog.add(WkErrorNotifyPopopWidget, {
                    title: _t('No Sky Wallet for selected customer'),
                    body: _t('Create a Sky Wallet for this customer before accepting wallet credit.'),
                });
            }

            // Case: Wallet credits not available
            // if (!partner.wallet_credits || partner.wallet_credits <= 0) {
            //     return this.dialog.add(WkErrorNotifyPopopWidget, {
            //         title: _t('Insufficient Wallet Balance'),
            //         body: _t("The customer's wallet does not have enough balance to cover the order amount."),
            //         wallet_credits: String(partner.wallet_credits),
            //     });
            // }

            // Proceed to apply wallet payment
            let existing_line = this.check_existing_wallet_line();
            let selected_paymentline;
            let result = undefined;
            if (existing_line) {
                current_order.select_paymentline(existing_line);
                selected_paymentline = current_order.get_selected_paymentline();
            } else {
                // Only add new wallet line if there is a due amount
                if (!due) {
                    return;
                }
                this.numberBuffer.reset();
                let skip = false;
                if(due > partner.wallet_credits){
                    this.pos.dialog.closeAll();
                    await this.dialog.add(WkErrorNotifyPopopWidget, {
                        title: _t('Insufficient Sky Wallet balance'),
                        body: _t("The customer's Sky Wallet does not have enough balance to cover the order amount."),
                        wallet_credits: String(partner.wallet_credits),
                        confirm: async ()=>{
                            result = await super.addNewPaymentLine(...arguments)
                            skip = true;
                            selected_paymentline = current_order.get_selected_paymentline();
                            if (selected_paymentline) {
                                selected_paymentline.set_amount(0); // Reset before applying
                                due = current_order.get_due(); // Recalculate due
                                const payment_amount = Math.min(due, partner.wallet_credits);
                                selected_paymentline.set_amount(payment_amount);
                                selected_paymentline.update({ is_wallet_payment_line: true });
                                // Update UI
                                $('.paymentline.selected .edit').text(this.env.utils.formatCurrency(payment_amount));
                                $('#use_wallet_payment').prop('checked', true);
                                $('div.wallet_balance').html(
                                    "Balance: <span style='color: #247b45;font-weight: bold;'>" +
                                    this.env.utils.formatCurrency(partner.wallet_credits - payment_amount) +
                                    "</span>"
                                );
                                this.render(true);
                            }
                        },
                    });
                    return;
                }
                if(!skip){
                    result = await super.addNewPaymentLine(...arguments);
                }
            }
            selected_paymentline = current_order.get_selected_paymentline();
            if (selected_paymentline) {
                selected_paymentline.set_amount(0); // Reset before applying
                due = current_order.get_due(); // Recalculate due
                const payment_amount = Math.min(due, partner.wallet_credits);
                selected_paymentline.set_amount(payment_amount);
                selected_paymentline.update({ is_wallet_payment_line: true });

                // Update UI
                $('.paymentline.selected .edit').text(this.env.utils.formatCurrency(payment_amount));
                $('#use_wallet_payment').prop('checked', true);
                $('div.wallet_balance').html(
                    "Balance: <span style='color: #247b45;font-weight: bold;'>" +
                    this.env.utils.formatCurrency(partner.wallet_credits - payment_amount) +
                    "</span>"
                );
                this.render(true);
            }
            return result;
        } catch (error) {
            console.error("Error in addNewPaymentLine:", error);
            this.dialog.add(AlertDialog, {
                title: _t("Payment Line Error"),
                body: _t("An unexpected error occurred while adding the payment line."),
            });
        }
    },

    async get_wallet_balance(){
        var self = this;
        var current_order = self.pos.get_order();
        var Partner = current_order.get_partner();
        self.hide_wallet_payment_method();
        if (Partner) {
            if (Partner.wallet_credits > 0 && !current_order.wallet_recharge_data && self.pos.wallet_method) {
                self.check_existing_wallet_line();
                $('div.wallet_balance').show();
                $('div.wallet_balance').html("Balance: <span style='color: #247b45;font-weight: bold;'>" + this.env.utils.formatCurrency(Partner.wallet_credits) + "</span>");
                $('div.use_wallet').show();
                $('#use_wallet_payment').change(async function (ev) {
                    if ($(this).is(":checked")) {                        
                        var paymentMethod = self.pos.wallet_method
                        await self.addNewPaymentLine(paymentMethod)
                        if (!self.check_existing_wallet_line())
                            $('#use_wallet_payment').prop('checked', false);
                    }
                    else {
                        if(self.check_existing_wallet_line() != null){
                            current_order.remove_paymentline(self.check_existing_wallet_line());
                        }
                        self.render(true);
                    }
                });
            } else {
                $('div.use_wallet').hide();
                $('div.wallet_balance').hide();
            }
        } else {
            $('div.wallet_balance').hide();
            $('div.use_wallet').hide();

        }
        var existing_wallet_line = self.check_existing_wallet_line();
        if (existing_wallet_line) {
            self.update_walletline_balance(existing_wallet_line);
        }
    },

    async wkOnMounted() {
        await this.get_wallet_balance()
    },

    update_walletline_balance(pline) {
        var self = this;
        var order = self.pos.get_order();
        var Partner = self.pos.get_order().get_partner();
        if (Partner && Partner.wallet_credits && Partner.wallet_credits > 0) {
            order.select_paymentline(pline);
            var pline_amount = pline.amount;
            pline.set_amount(0);
            var due = self.pos.get_order().get_due();
            var payment_amount = Math.min(due, pline_amount, Partner.wallet_credits);
            pline.set_amount(payment_amount);
            pline.update({'is_wallet_payment_line': true});
            self.render(true);
            $('.paymentline.selected .edit').text(this.env.utils.formatCurrency(payment_amount));
            $('#use_wallet_payment').prop('checked', true);
            $('div.wallet_balance').html("Balance: <span style='color: #247b45;font-weight: bold;'>" + this.env.utils.formatCurrency(Partner.wallet_credits - payment_amount) + "</span>");
        }
        else {
            order.remove_paymentline(pline);
            this.numberBuffer.reset();
            self.render(true);
        }
    },

    hide_wallet_payment_method() {
        var self = this;
        var current_order = self.pos.get_order();
        if (current_order && self.pos.wallet_method) {
            var wallet_method_id = self.pos.wallet_method.id;
            var find_string = '[data-id=' + wallet_method_id.toString() + ']';
            var wallet_paymentmethods = ($('.paymentmethods').find(find_string)[0]);
            if (current_order && current_order.wallet_recharge_data && self.pos.wallet_method || !(current_order && current_order.get_partner() && current_order.get_partner().wallet_credits))
                $(wallet_paymentmethods).hide();
            else
                $(wallet_paymentmethods).show();
        }
    },

    show_wallet_payment_method() {
        var self = this;
        var wallet_method_id = self.pos.wallet_method.id;
        var find_string = '[data-id=' + wallet_method_id.toString() + ']';
        var wallet_paymentmethods = ($('.paymentmethods').find(find_string)[0]);
        if (wallet_paymentmethods)
            $(wallet_paymentmethods).show();

    },

    async validateOrder(isForceValidate) {
        var self = this;
        var current_order = self.pos.get_order();
        await super.validateOrder(...arguments);
        if (current_order.is_paid()) {
            if (current_order && current_order.wallet_recharge_data && self.pos.wallet_product) {
                var partner = current_order.get_partner();
                var amount = 0.0;
                current_order.get_orderlines().forEach(function (orderline) {
                    if (orderline.product_id.id == self.pos.wallet_product.id) {
                        amount = amount + parseFloat(orderline.get_display_price());
                    }
                });
                partner.wallet_credits = round_di(parseFloat(partner.wallet_credits) + amount, 3);
            }
            else if (current_order && self.pos.wallet_method && current_order.get_partner()) {
                var plines = current_order.payment_ids;
                var amount = 0.0;
                var partner = current_order.get_partner();
                if(plines && plines.length){
                    plines.forEach(function (pline) {
                        if (pline.payment_method_id.id == self.pos.wallet_method.id) {
                            amount = amount + parseFloat(pline.amount);
                        }
                    });
                }
                partner.wallet_credits = round_di(parseFloat(partner.wallet_credits) - amount, 3);
            }
        }
    },   
    async _selectPartner(){
        await this.pos.selectPartner();
        await this.get_wallet_balance();
    },
    
    async updateSelectedPaymentline(amount = false) {
        await this.get_wallet_balance();
        return await super.updateSelectedPaymentline(amount);
    },

    async afterOrderValidation(suggestToSync = true) {
        
        let partner = this.currentOrder.get_partner();
        if (this.pos.wallet_product && partner) {
            if(partner.wallet_id){
                await this.pos.data.read("pos.wallet", [partner.wallet_id.id]);
            }
        }
        return  await super.afterOrderValidation(suggestToSync);
    },

})
