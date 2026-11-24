/** @odoo-module */

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

// Odoo 20 port: store/hook modules moved (app/services, app/hooks), order API is camelCase,
// lines are added by product template, and relational fields are records.

import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { MainWalletRechargePopup } from "@pos_wallet_management/app/popup/MainWalletRechargePopup";
import { WkErrorNotifyPopopWidget } from "@pos_wallet_management/app/popup/WkErrorNotifyPopopWidget";
import { _t } from "@web/core/l10n/translation";
import { DataServiceOptions } from "@point_of_sale/app/models/data_service_options";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { WkWalletRechargePopup } from "@pos_wallet_management/app/popup/WkWalletRechargePopup";

patch(DataServiceOptions.prototype, {
    get databaseIndex() {
        return {
            ...super.databaseIndex,
            "pos.wallet": ["nfcid"],
        };
    },
});

patch(PosOrder.prototype, {
    /** Payment line paid with the Sky Wallet method, if any. */
    getWalletPaymentLine(pos) {
        if (!pos.wallet_method) {
            return null;
        }
        return this.payment_ids.find((line) => line.payment_method_id?.id === pos.wallet_method.id) || null;
    },

    setPartnerForWallet(partner, pos) {
        this.setPartner(partner);
        const walletLine = this.getWalletPaymentLine(pos);
        if (walletLine) {
            this.removePaymentline(walletLine);
        }
        return true;
    },

    get isWalletRecharge() {
        return Boolean(this.wallet_recharge_data);
    },
});

patch(PosStore.prototype, {
    async processServerData() {
        await super.processServerData(...arguments);
        this.wallet_method = this.models["pos.payment.method"].getAll().find((pm) => pm.wallet_method) || null;
        this.wallet_product = this.models["product.product"].getAll().find((p) => p.default_code === "wk_wallet") || null;
        this._loadWalletsData();
    },

    _loadWalletsData() {
        this.all_wallets = this.models["pos.wallet"].getAll().sort((a, b) => b.id - a.id);
        this.wallet_by_name = {};
        for (const wallet of this.all_wallets) {
            this.wallet_by_name[wallet.name] = wallet;
        }
    },

    showWalletMethodMissing() {
        this.dialog.add(WkErrorNotifyPopopWidget, {
            title: _t("Sky Wallet payment method not found"),
            body: _t("Please configure the Sky Wallet payment method in Point of Sale settings."),
        });
    },

    async rechargeWallet(wallet_id) {
        if (!this.wallet_method) {
            return this.showWalletMethodMissing();
        }
        this.dialog.add(MainWalletRechargePopup, { wallet_id: wallet_id || "" });
    },

    openWalletRecharge() {
        if (!this.wallet_method) {
            return this.showWalletMethodMissing();
        }
        const partner = this.getOrder()?.getPartner();
        if (partner) {
            this.dialog.add(WkWalletRechargePopup, { partner });
        }
    },

    _isWalletProductVals(vals) {
        if (!this.wallet_product) {
            return false;
        }
        const product = vals.product_id;
        const productId = typeof product === "number" ? product : product?.id;
        if (productId) {
            return productId === this.wallet_product.id;
        }
        const tmpl = vals.product_tmpl_id;
        const tmplId = typeof tmpl === "number" ? tmpl : tmpl?.id;
        return tmplId === this.wallet_product.product_tmpl_id?.id;
    },

    async addLineToCurrentOrder(vals, opts = {}, configure = true) {
        const order = this.getOrder();
        const isWalletProduct = this._isWalletProductVals(vals);
        if (isWalletProduct && !order?.isWalletRecharge) {
            // The recharge product is only sold through the recharge popup.
            this.dialog.add(MainWalletRechargePopup, { wallet_id: "" });
            return;
        }
        if (!isWalletProduct && order?.isWalletRecharge) {
            this.dialog.add(AlertDialog, {
                title: _t("Sky Wallet recharge"),
                body: _t("A Sky Wallet recharge order can only contain the recharge. Start a new order for products."),
            });
            return;
        }
        return await super.addLineToCurrentOrder(...arguments);
    },

    isWalletOrderline(order = this.getOrder()) {
        if (!order || !this.wallet_product) {
            return false;
        }
        return order.getOrderlines().some((line) => line.product_id?.id === this.wallet_product.id);
    },

    async selectPartner(currentOrder = this.getOrder()) {
        if (currentOrder?.isWalletRecharge && this.isWalletOrderline(currentOrder)) {
            this.dialog.add(AlertDialog, {
                title: _t("Customer Change Not Allowed!"),
                body: _t("Oops! You can't change the customer for a wallet recharge order."),
            });
            return currentOrder.getPartner();
        }
        return await super.selectPartner(...arguments);
    },

    /** Re-read the customer and wallet after the server has debited/credited the wallet. */
    async refreshWalletPartner(partner) {
        if (!partner || !this.wallet_method) {
            return;
        }
        try {
            await this.data.read("res.partner", [partner.id]);
            const walletId = partner.wallet_id?.id;
            if (walletId) {
                await this.data.read("pos.wallet", [walletId]);
            }
            this._loadWalletsData();
        } catch (error) {
            // Offline: the balance refreshes on the next successful read.
            console.warn("Sky Wallet balance refresh failed", error);
        }
    },
});
