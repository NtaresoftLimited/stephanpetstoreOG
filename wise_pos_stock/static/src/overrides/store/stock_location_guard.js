/** @odoo-module */
/**
 * Stephan's Pet Store: keep POS stock scoped to the till's own location (wise_pos_stock).
 *
 * Problem: wise_pos_stock loads `qty_available` for the till location (pos.config.in_stock_pick,
 * e.g. MASAK/Stock) on start and on its refresh timer, but every other product fetch made by the
 * POS (product search, barcode lookup, variant loading: product.product search_read / read)
 * returns Odoo's company-wide `qty_available` (MASAK + MBS + MIKOC) and overwrites the location
 * value in memory. The out-of-stock checks then see e.g. 532 instead of -3 and allow the sale.
 *
 * Fix:
 *  1. Every product.product read/search_read from the POS carries context {location: <till
 *     location>}, so Odoo computes qty_available/virtual_available for that location only.
 *  2. Before opening payment, fresh stock for the order's products is fetched from the server
 *     for the till location and the whole order is checked (quantities summed per product).
 */
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { PosData } from "@point_of_sale/app/models/data_service";
import { PosStore } from "@point_of_sale/app/store/pos_store";
import { getProductQty } from "../../utils";

function tillStockLocationId(config) {
    const id = Number(config?.in_stock_pick || 0);
    return id > 0 ? id : false;
}

patch(PosData.prototype, {
    async execute(params) {
        if (
            params &&
            params.model === "product.product" &&
            (params.type === "search_read" || params.type === "read")
        ) {
            const config = this.models?.["pos.config"]?.getFirst?.();
            const location = tillStockLocationId(config);
            if (location) {
                const options =
                    params.options && !Array.isArray(params.options) ? { ...params.options } : {};
                options.context = { ...(options.context || {}), location };
                params = { ...params, options };
            }
        }
        return super.execute(params);
    },
});

patch(PosStore.prototype, {
    async pay() {
        if (this.config.is_restrict_out_of_stock_products) {
            const order = this.get_order();
            const lines = order?.get_orderlines?.() || order?.lines || [];
            const requested = new Map(); // product -> total qty on this order
            for (const line of lines) {
                const product = line.product_id || line.product;
                if (!product || product.type === "service") {
                    continue;
                }
                const qty = Number(line.quantity ?? line.qty ?? 0);
                requested.set(product, (requested.get(product) || 0) + qty);
            }

            const location = tillStockLocationId(this.config);
            if (requested.size && location) {
                try {
                    const products = [...requested.keys()];
                    const fresh = await this.data.call("product.product", "wise_get_product_info_pos", [
                        location,
                        products.map((p) => p.id),
                    ]);
                    for (const product of products) {
                        const data = fresh?.[product.id];
                        if (data) {
                            product.qty_available = data.qty_available;
                            product.virtual_available = data.virtual_available;
                        }
                    }
                } catch (error) {
                    // Offline / server unreachable: fall back to the quantities already on screen.
                    console.warn("Could not refresh till stock before payment:", error);
                }
            }

            const short = [];
            for (const [product, qty] of requested) {
                if (qty <= 0) {
                    continue; // returns/refund lines
                }
                const available = getProductQty(this.config.stock_type, product);
                if (available < qty) {
                    short.push(
                        `"${product.display_name || product.name}" (Stock: ${available}, Ordered: ${qty})`
                    );
                }
            }
            if (short.length) {
                this.notification.add(_t("Insufficient Stock: ") + short.join(", "), {
                    type: "danger",
                });
                return;
            }
        }
        return super.pay(...arguments);
    },
});
