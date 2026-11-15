import { Component, proxy, t, useProps } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { wiseIsTracked } from "./stock_utils";

/** Products at or below the low-stock threshold at this till's location. */
export class LowStockDialog extends Component {
    static template = "wise_pos_stock.LowStockDialog";
    static components = { Dialog };
    props = useProps({ close: t.function() });

    setup() {
        this.pos = usePos();
        this.state = proxy({ search: "", refreshing: false });
    }

    get threshold() {
        return this.pos.config.low_stock_threshold || 0;
    }

    get rows() {
        const search = this.state.search.trim().toLowerCase();
        const rows = [];
        for (const tmpl of this.pos.models["product.template"].getAll()) {
            if (!tmpl.available_in_pos || !tmpl.active || !wiseIsTracked(tmpl)) {
                continue;
            }
            const qty = this.pos.wiseTemplateQty(tmpl);
            if (qty > this.threshold) {
                continue;
            }
            const name = tmpl.display_name || tmpl.name || "";
            if (search && !name.toLowerCase().includes(search) && !(tmpl.default_code || "").toLowerCase().includes(search)) {
                continue;
            }
            rows.push({ id: tmpl.id, name, code: tmpl.default_code || "", qty });
        }
        return rows.sort((a, b) => a.qty - b.qty || a.name.localeCompare(b.name));
    }

    async refresh() {
        this.state.refreshing = true;
        await this.pos.wiseRefreshStock();
        this.state.refreshing = false;
    }
}
