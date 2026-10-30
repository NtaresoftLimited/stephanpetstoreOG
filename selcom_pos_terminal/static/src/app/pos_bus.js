/** @odoo-module */
import { patch } from "@web/core/utils/patch";
import { PosStore } from "@point_of_sale/app/store/pos_store";

patch(PosStore.prototype, {
    async setup() {
        await super.setup(...arguments);
        this.data.connectWebSocket("SELCOM_TERMINAL_RESPONSE", () => {
            const pendingLine = this.getPendingPaymentLine("selcom");
            if (pendingLine) {
                this
                .getPendingPaymentLine("selcom")
                .payment_method_id.payment_terminal.handleSelcomStatusResponse();
            }
        });

    },
});


