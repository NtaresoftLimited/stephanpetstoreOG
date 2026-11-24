import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { PosStore } from "@point_of_sale/app/services/pos_store";
import { wiseStock, wiseIsTracked, wiseTemplate, checkMarginRestriction } from "./stock_utils";
import { LowStockDialog } from "./low_stock_dialog";

patch(PosStore.prototype, {
    async afterProcessServerData() {
        const result = await super.afterProcessServerData(...arguments);
        wiseStock.pos = this;
        this.wiseStockData = { products: {}, templates: {}, loaded: false };
        await this.wiseRefreshStock();
        this.wiseStartStockTimer();
        return result;
    },

    get wiseStockEnabled() {
        const c = this.config;
        return Boolean(c.is_display_stock || c.is_restrict_out_of_stock_products ||
            c.only_in_stock_products || c.is_low_stock_screen_visible);
    },

    /** Load till-location stock from the server (all products, or only the given templates). */
    async wiseRefreshStock(templateIds = null) {
        if (!this.wiseStockEnabled) {
            return;
        }
        try {
            const data = await this.data.call("product.template", "wise_get_pos_stock", [
                this.config.id,
                templateIds,
            ]);
            const current = this.wiseStockData || { products: {}, templates: {} };
            this.wiseStockData = {
                products: templateIds ? { ...current.products, ...data.products } : data.products,
                templates: templateIds ? { ...current.templates, ...data.templates } : data.templates,
                loaded: true,
            };
        } catch (error) {
            // Offline or server error: keep the last known quantities.
            console.warn("wise_pos_stock: could not refresh stock", error);
        }
    },

    wiseStartStockTimer() {
        clearInterval(this._wiseStockTimer);
        if (!this.wiseStockEnabled) {
            return;
        }
        const minutes = parseInt(this.config.stock_quantities_refresh_rate || "1", 10) || 1;
        this._wiseStockTimer = setInterval(() => this.wiseRefreshStock(), minutes * 60 * 1000);
    },

    wiseProductQty(product) {
        return Number(this.wiseStockData?.products?.[product.id] ?? 0);
    },

    wiseTemplateQty(tmpl) {
        return Number(this.wiseStockData?.templates?.[tmpl.id] ?? 0);
    },

    /** Quantity of a product already on the order (all lines, refunds included). */
    wiseOrderQty(product, order = this.getOrder()) {
        let total = 0;
        for (const line of order?.lines || []) {
            if (line.product_id?.id === product.id) {
                total += Number(line.qty || 0);
            }
        }
        return total;
    },

    wiseShortages(order) {
        const requested = new Map();
        for (const line of order?.lines || []) {
            if (wiseIsTracked(line.product_id)) {
                requested.set(line.product_id, (requested.get(line.product_id) || 0) + Number(line.qty || 0));
            }
        }
        const short = [];
        for (const [product, qty] of requested) {
            const available = this.wiseProductQty(product);
            if (qty > 0 && qty > available) {
                short.push({ product, available, requested: qty });
            }
        }
        return short;
    },

    wiseNotifyNoStock(name, available) {
        this.notification.add(
            _t('Insufficient Stock: "%(name)s" has only %(qty)s available at this location.', {
                name,
                qty: available,
            }),
            { type: "danger" }
        );
    },

    // Hide out-of-stock goods when "Only In-Stock Products" is on.
    filterExcludedProducts(products) {
        if (!this.config.only_in_stock_products || !this.wiseStockData?.loaded) {
            return super.filterExcludedProducts(products);
        }
        const self = this;
        function* inStock() {
            for (const product of products) {
                if (!wiseIsTracked(product) || self.wiseTemplateQty(product) > 0) {
                    yield product;
                }
            }
        }
        return super.filterExcludedProducts(inStock());
    },

    // Tapping a card or scanning a barcode.
    async canAddProductToCurrentOrder(product) {
        if (!(await super.canAddProductToCurrentOrder(...arguments))) {
            return false;
        }
        const tmpl = wiseTemplate(product);
        const margin = checkMarginRestriction(tmpl, this.config);
        if (margin) {
            if (margin.blocked) {
                this.dialog.add(AlertDialog, {
                    title: _t("Low Margin"),
                    body: _t('"%(name)s" cannot be sold: %(reason)s.', { name: tmpl.display_name, reason: margin.reason }),
                });
                return false;
            }
            this.notification.add(_t("Low margin: %s", margin.reason), { type: "warning" });
        }
        if (!this.config.is_restrict_out_of_stock_products || !wiseIsTracked(tmpl)) {
            return true;
        }
        const variants = tmpl.product_variant_ids || [];
        if (variants.length > 1) {
            // The variant is chosen afterwards; addLineToOrder checks it.
            if (this.wiseTemplateQty(tmpl) <= 0) {
                this.wiseNotifyNoStock(tmpl.display_name, this.wiseTemplateQty(tmpl));
                return false;
            }
            return true;
        }
        const variant = variants[0];
        const available = this.wiseProductQty(variant);
        if (this.wiseOrderQty(variant) + 1 > available) {
            this.wiseNotifyNoStock(tmpl.display_name, available);
            return false;
        }
        return true;
    },

    // Every way of adding a line ends here (variants, combos, sale-order import, ...).
    async addLineToOrder(vals, order, opts = {}, configure = true) {
        const line = await super.addLineToOrder(...arguments);
        if (!line || !this.config.is_restrict_out_of_stock_products || !wiseIsTracked(line.product_id)) {
            return line;
        }
        const product = line.product_id;
        const available = this.wiseProductQty(product);
        const inOrder = this.wiseOrderQty(product, order);
        if (line.qty > 0 && inOrder > available) {
            const excess = inOrder - Math.max(available, 0);
            if (line.qty - excess > 0) {
                line.setQuantity(line.qty - excess, true);
            } else {
                order.removeOrderline(line);
            }
            this.wiseNotifyNoStock(product.display_name, available);
            return false;
        }
        return line;
    },

    // Final check with fresh server stock before the payment screen opens.
    async pay() {
        const order = this.getOrder();
        if (order && this.config.is_restrict_out_of_stock_products) {
            const templateIds = [
                ...new Set(
                    order.lines.filter((l) => wiseIsTracked(l.product_id)).map((l) => wiseTemplate(l.product_id).id)
                ),
            ];
            if (templateIds.length) {
                await this.wiseRefreshStock(templateIds);
            }
            const short = this.wiseShortages(order);
            if (short.length) {
                this.dialog.add(AlertDialog, {
                    title: _t("Insufficient Stock"),
                    body:
                        _t("The order is more than the stock at this location:") +
                        "\n" +
                        short
                            .map((s) => `• ${s.product.display_name}: available ${s.available}, ordered ${s.requested}`)
                            .join("\n"),
                });
                return;
            }
        }
        return super.pay(...arguments);
    },

    wiseOpenLowStock() {
        this.dialog.add(LowStockDialog, {});
    },
});
