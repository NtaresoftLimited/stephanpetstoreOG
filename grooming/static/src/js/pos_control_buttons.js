/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { useService } from "@web/core/utils/hooks";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { RequestStockPopup } from "@grooming/js/request_stock_popup";

import { ReplenishmentRequestPopup } from "@grooming/js/replenishment_request_popup";

patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments);
        this.dialog = useService("dialog");
        this.orm = useService("orm");
        this.notification = useService("notification");
    },
    
    async clickRequestStock() {
        this.dialog.add(RequestStockPopup, {
            title: 'Request Stock',
            pos: this.pos
        });
    },

    async clickReplenishmentRequest() {
        this.dialog.add(ReplenishmentRequestPopup, {
            title: 'Replenishment Request',
            pos: this.pos
        });
    }
});
