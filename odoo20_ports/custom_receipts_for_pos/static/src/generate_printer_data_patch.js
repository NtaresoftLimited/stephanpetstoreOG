import { GeneratePrinterData } from "@point_of_sale/app/utils/printer/generate_printer_data";
import { patch } from "@web/core/utils/patch";

// Till-side receipt data; keep in sync with PosOrder.order_receipt_generate_data (Python).
patch(GeneratePrinterData.prototype, {
    generateReceiptData() {
        const data = super.generateReceiptData(...arguments);
        data.extra_data.stephans_change = this.formatCurrency(this.order.amount_return || 0);
        return data;
    },
});
