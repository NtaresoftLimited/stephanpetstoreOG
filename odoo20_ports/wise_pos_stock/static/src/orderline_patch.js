import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { wiseStock, wiseIsTracked } from "./stock_utils";

// Raising a line's quantity (numpad, +) above the till stock is refused, like in Odoo 18.
patch(PosOrderline.prototype, {
    setQuantity(quantity, keep_price) {
        const pos = wiseStock.pos;
        const target = typeof quantity === "number" ? quantity : parseFloat("" + (quantity || 0));
        if (
            pos?.config?.is_restrict_out_of_stock_products &&
            wiseIsTracked(this.product_id) &&
            target > 0 &&
            target > Number(this.qty || 0)
        ) {
            const available = pos.wiseProductQty(this.product_id);
            const otherLines = pos.wiseOrderQty(this.product_id, this.order_id) - Number(this.qty || 0);
            if (otherLines + target > available) {
                return {
                    title: _t("Insufficient Stock"),
                    body: _t('"%(name)s" has only %(qty)s available at this location.', {
                        name: this.product_id.display_name,
                        qty: available,
                    }),
                };
            }
        }
        return super.setQuantity(...arguments);
    },
});
