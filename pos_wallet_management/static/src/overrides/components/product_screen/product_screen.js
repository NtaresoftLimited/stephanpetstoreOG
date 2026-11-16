/** @odoo-module */

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

// Odoo 20 port: a scanned code that matches a Sky Wallet NFC card opens the wallet popup;
// anything else goes to the normal product barcode handling. Recharge orders are guarded in
// PosStore.addLineToCurrentOrder instead of greying the product pane through jQuery.

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { NFCScanWalletPopup } from "@pos_wallet_management/app/popup/NFCScanWalletPopup/NFCScanWalletPopup";

patch(ProductScreen.prototype, {
    async _findWalletByCard(code) {
        const nfcid = code?.code;
        if (!nfcid || !this.pos.wallet_method) {
            return null;
        }
        const local = this.pos.models["pos.wallet"].getBy("nfcid", nfcid);
        if (local) {
            return local;
        }
        // Only ask the server when the code is not a known product (keeps product scans fast/offline-safe).
        if (await this._getProductByBarcode(code)) {
            return null;
        }
        try {
            const ids = await this.pos.data.call("pos.wallet", "search", [[["nfcid", "=", nfcid], ["state", "=", "confirm"]]], {});
            if (ids.length) {
                await this.pos.data.read("pos.wallet", [ids[0]]);
                return this.pos.models["pos.wallet"].getBy("id", ids[0]);
            }
        } catch {
            // Offline: fall through to the normal "not found" handling.
        }
        return null;
    },

    async _barcodeProductAction(code) {
        const wallet = await this._findWalletByCard(code);
        if (wallet) {
            this.dialog.add(NFCScanWalletPopup, {
                wallet,
                getPayload: () => wallet.partner_id,
                formatCurrency: (amount) => this.pos.formatCurrency(amount),
            });
            return;
        }
        return await super._barcodeProductAction(...arguments);
    },
});
