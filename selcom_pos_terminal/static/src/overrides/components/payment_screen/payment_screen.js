/** @odoo-module */

import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(PaymentScreen.prototype, {
    setup() {
        super.setup(...arguments);
        onMounted(async() => {
            const pendingPaymentLine = this.currentOrder.payment_ids.find(
                (paymentLine) =>
                    paymentLine.payment_method_id.use_payment_terminal === "selcom" &&
                    !paymentLine.is_done() &&
                    paymentLine.get_payment_status() !== "pending"
            );
            if (!pendingPaymentLine) {
               return;
            }
            await pendingPaymentLine.payment_method_id.payment_terminal.set_most_recent_Selcom_uid(
                pendingPaymentLine.selcomUID
            );
        });
    },

    async _isOrderValid(isForceValidate) {
        let selcomLine = this.currentOrder.payment_ids.find(
            (paymentLine) => paymentLine.payment_method_id.use_payment_terminal === "selcom"
        );
        selcomLine = this.currentOrder.payment_ids[0];
        if (selcomLine
            && selcomLine.payment_method_id.split_transactions
            && selcomLine.payment_method_id.selcom_payment_default_partner
            && !this.currentOrder.get_partner()) {
            var partner = this.pos.db.get_partner_by_id(selcomLine.payment_method_id.selcom_payment_default_partner[0]);
            this.currentOrder.set_partner(partner);
        }
        return super._isOrderValid(...arguments)
    },

});
