/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { useService } from "@web/core/utils/hooks";
import { RequestStockPopup } from "@grooming/js/request_stock_popup";
import { ReplenishmentRequestPopup } from "@grooming/js/replenishment_request_popup";
import { PosAccessRightPlugin } from "@point_of_sale/app/plugins/access_right_plugin";

// Buttons production (Odoo 18) hides in the POS "Actions" dialog: Quotation / Order (pos_sale),
// Enter Code and Reward (pos_loyalty). Odoo 20 gates them on these access-right getters.
// pos_hr re-defines the getters without calling super and loads after this module, so the patch is
// applied once at runtime (first ControlButtons setup), when it is sure to be the outermost one.
// Discount is left alone: pos_dynamic_discount enforces its limits on that button.
const HIDDEN_ACTIONS = {
    get canAccessQuotation() {
        return false;
    },
    get canApplyPromoCode() {
        return false;
    },
    get canApplyRewards() {
        return false;
    },
};
let hiddenActionsPatched = false;
function hideProductionHiddenActions() {
    if (!hiddenActionsPatched) {
        patch(PosAccessRightPlugin.prototype, HIDDEN_ACTIONS);
        hiddenActionsPatched = true;
    }
}

patch(ControlButtons.prototype, {
    setup() {
        hideProductionHiddenActions();
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
