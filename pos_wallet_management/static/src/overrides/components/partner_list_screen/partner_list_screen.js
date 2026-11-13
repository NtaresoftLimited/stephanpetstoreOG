/** @odoo-module */
/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";
import { PartnerList } from "@point_of_sale/app/screens/partner_list/partner_list";

patch(PartnerList.prototype, {
    setup() {
        super.setup();
        // onMounted(this.OnMounted);
    },
    OnMounted() {
        var self = this;
        
        var current_order = self.pos.get_order();
        if (current_order != null && current_order.wallet_recharge_data) {
            if (self.is_wallet_orderline()){
                this.dialog
            }
            else{
                current_order.wallet_recharge_data = null;
            }
        }
    },
    is_wallet_orderline() {
        var self = this;
        var current_order = self.pos.get_order();
        var wallet_line = false;
        
        if (current_order.get_orderlines() && self.pos.wallet_product) {
            current_order.get_orderlines().forEach(function (orderline) {
                if (orderline.product_id.id == self.pos.wallet_product.id)
                    wallet_line = true;
            });
        }
        return wallet_line;
    },
});
