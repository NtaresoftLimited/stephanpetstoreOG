/** @odoo-module */

/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */

import { Navbar } from "@point_of_sale/app/navbar/navbar";
import { WalletRechargeWidget } from "@pos_wallet_management/overrides/components/product_screen/WalletRechargeWidget";
import { patch } from "@web/core/utils/patch";

patch(Navbar, {
    components: { ...Navbar.components, WalletRechargeWidget },
});
