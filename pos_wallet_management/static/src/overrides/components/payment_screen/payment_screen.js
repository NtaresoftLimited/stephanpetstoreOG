/** @odoo-module */

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

// Odoo 20 port: the wallet switch is rendered reactively from getters (no jQuery DOM edits),
// order validation lives in OrderPaymentValidation, and NFC cards are read through barcode_reader.

import { _t } from "@web/core/l10n/translation";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { useBarcodeReader } from "@point_of_sale/app/hooks/barcode_reader_hook";
import OrderPaymentValidation from "@point_of_sale/app/utils/order_payment_validation";
import { WkErrorNotifyPopopWidget } from "@pos_wallet_management/app/popup/WkErrorNotifyPopopWidget";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        useBarcodeReader({ product: (code) => this._onWalletCardScanned(code) });
    },

    get walletPartner() {
        return this.currentOrder?.getPartner() || null;
    },

    get walletLine() {
        return this.currentOrder?.getWalletPaymentLine(this.pos) || null;
    },

    get walletCredits() {
        return this.walletPartner?.wallet_credits || 0;
    },

    get walletRemaining() {
        return this.walletCredits - (this.walletLine?.amount || 0);
    },

    get showWalletSwitch() {
        return Boolean(
            this.pos.wallet_method &&
                this.pos.config.show_wallet_type === "checkbox" &&
                this.walletPartner?.wallet_id &&
                this.walletCredits > 0 &&
                !this.currentOrder.isWalletRecharge
        );
    },

    get displayedPaymentMethods() {
        const methods = super.displayedPaymentMethods;
        const walletMethod = this.pos.wallet_method;
        if (!walletMethod) {
            return methods;
        }
        const hideWallet =
            this.pos.config.show_wallet_type === "checkbox" ||
            this.currentOrder?.isWalletRecharge ||
            !(this.walletCredits > 0);
        return hideWallet ? methods.filter((pm) => pm.id !== walletMethod.id) : methods;
    },

    async toggleWalletPayment(ev) {
        if (ev.target.checked) {
            await this.addNewPaymentLine(this.pos.wallet_method);
        } else if (this.walletLine) {
            this.currentOrder.removePaymentline(this.walletLine);
            this.numberBuffer.reset();
        }
    },

    _applyWalletAmount(line, partner) {
        line.setAmount(0);
        const amount = Math.max(0, Math.min(this.currentOrder.remainingDue, partner.wallet_credits));
        line.setAmount(amount);
        this.numberBuffer.set(amount.toString());
    },

    async addNewPaymentLine(paymentMethod, args = {}) {
        if (!paymentMethod?.wallet_method) {
            return await super.addNewPaymentLine(...arguments);
        }
        const order = this.currentOrder;
        const partner = order.getPartner();
        if (!partner) {
            this.dialog.add(AlertDialog, {
                title: _t("Customer required"),
                body: _t("Select a customer before using Sky Wallet."),
            });
            return false;
        }
        if (!partner.wallet_id) {
            this.dialog.add(WkErrorNotifyPopopWidget, {
                title: _t("No Sky Wallet for selected customer"),
                body: _t("Create a Sky Wallet for this customer before accepting wallet credit."),
            });
            return false;
        }
        const existing = this.walletLine;
        if (existing) {
            order.selectPaymentline(existing);
            return true;
        }
        if (!(order.remainingDue > 0)) {
            return false;
        }
        if (!(partner.wallet_credits > 0)) {
            this.dialog.add(WkErrorNotifyPopopWidget, {
                title: _t("Insufficient Sky Wallet balance"),
                body: _t("The customer's Sky Wallet has no balance."),
            });
            return false;
        }
        const addCapped = async () => {
            const added = await super.addNewPaymentLine(paymentMethod, args);
            const line = this.walletLine;
            if (added && line) {
                order.selectPaymentline(line);
                this._applyWalletAmount(line, partner);
            }
            return added;
        };
        if (order.remainingDue > partner.wallet_credits) {
            // Offer a partial wallet payment; the rest is paid with another method.
            this.dialog.add(WkErrorNotifyPopopWidget, {
                title: _t("Insufficient Sky Wallet balance"),
                body: _t("The customer's Sky Wallet does not cover the full amount. Continue to pay part of it from the wallet."),
                wallet_credits: this.pos.formatCurrency(partner.wallet_credits),
                confirm: addCapped,
            });
            return false;
        }
        return await addCapped();
    },

    updateSelectedPaymentline(amount = false) {
        const res = super.updateSelectedPaymentline(...arguments);
        const line = this.selectedPaymentLine;
        const partner = this.walletPartner;
        if (line && partner && line.payment_method_id?.wallet_method && line.amount > partner.wallet_credits) {
            // Never take more from the wallet than its balance.
            line.setAmount(partner.wallet_credits);
            this.numberBuffer.set(String(partner.wallet_credits));
        }
        return res;
    },

    async _onWalletCardScanned(code) {
        const nfcid = code?.code;
        if (!nfcid || !this.pos.wallet_method) {
            return;
        }
        let wallet = this.pos.models["pos.wallet"].getBy("nfcid", nfcid);
        if (!wallet) {
            try {
                const ids = await this.pos.data.call("pos.wallet", "search", [[["nfcid", "=", nfcid], ["state", "=", "confirm"]]], {});
                if (ids.length) {
                    await this.pos.data.read("pos.wallet", [ids[0]]);
                    wallet = this.pos.models["pos.wallet"].getBy("id", ids[0]);
                }
            } catch {
                return; // offline
            }
        }
        const order = this.currentOrder;
        if (!wallet || !order) {
            return;
        }
        if (this.pos.isWalletOrderline(order)) {
            this.dialog.add(AlertDialog, {
                title: _t("Not Allowed !"),
                body: _t("Sky Wallet recharge using an NFC card is not allowed."),
            });
            return;
        }
        order.setPartner(wallet.partner_id);
        await this.addNewPaymentLine(this.pos.wallet_method);
    },
});

patch(OrderPaymentValidation.prototype, {
    async afterOrderValidation() {
        const res = await super.afterOrderValidation(...arguments);
        const partner = this.order?.getPartner();
        if (partner && (this.order.isWalletRecharge || this.order.getWalletPaymentLine(this.pos))) {
            await this.pos.refreshWalletPartner(partner);
        }
        return res;
    },
});
