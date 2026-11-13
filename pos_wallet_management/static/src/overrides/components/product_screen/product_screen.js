/** @odoo-module **/

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";
import { NFCScanWalletPopup } from "@pos_wallet_management/app/popup/NFCScanWalletPopup/NFCScanWalletPopup";

patch(ProductScreen.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(this.onMounted);

    },
    onMounted() {
        var self = this;
        var current_order = self.pos.get_order();
        if (current_order != null && current_order.wallet_recharge_data) {
            $('.rightpane').css("pointer-events", "none");
            $('.rightpane').css("opacity", "0.3");
        }
        else {
            $('.rightpane').css("pointer-events", "");
            $('.rightpane').css("opacity", "");
        }
    },

    async _barcodeProductAction(code) {
        const nfcid = code.code;
        let wallet = this.pos.models["pos.wallet"].getBy("nfcid", nfcid);
        if (!wallet) {
            const ids = await this.pos.data.call("pos.wallet", "search", [[["nfcid", "=", nfcid]]], {});
            if (ids.length) {
                await this.pos.data.read("pos.wallet", [ids[0]]);
                wallet = this.pos.models["pos.wallet"].getBy("id", ids[0]);
            }
        }
        if(wallet){
            await this.dialog.add(NFCScanWalletPopup,{
                wallet: wallet,
                getPayload: (data) => {
                    return wallet.partner_id;
                },
                formatCurrency: this.pos.env.utils.formatCurrency,
            })
        }
        else{
            await super._barcodeProductAction(code);
        }
    }

})
