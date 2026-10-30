/** @odoo-module */

import { ProductScreen } from "@point_of_sale/app/screens/product_screen/product_screen";
import { useService } from "@web/core/utils/hooks";
import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";

export class ZReportButton extends Component {
    static template = "custom_pos_reports.ZReportButton";

    setup() {
        this.orm = useService("orm");
        this.report = useService("report");
        this.pos = useService("pos");
    }

    async onClick() {
        // Get current session ID
        const session_id = this.pos.pos_session.id;

        try {
            // Call backend method to generate report URL
            const result = await this.orm.call(
                "pos.session", // Model
                "action_generate_z_report_thermal", // Method
                [[session_id]] // Args
            );

            if (result && result.url) {
                // Determine base URL
                const url = result.url;

                // Open PDF in new tab
                // We use the report service to download/print
                // this.report.doAction(result); // This is standard way

                // Since result is an 'ir.actions.act_url', doAction handles it.
                // However, doAction might fail inside POS if not configured strictly.
                // Simpler: Just window.open
                window.open(url, '_blank');
            } else {
                console.error("No URL returned for Z-Report");
            }

        } catch (e) {
            console.error("Z-Report Error:", e);
        }
    }
}

ProductScreen.addControlButton({
    component: ZReportButton,
    condition: function () {
        return true;
    },
});
