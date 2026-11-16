import { patch } from "@web/core/utils/patch";
import { usePos } from "@point_of_sale/app/hooks/pos_hook";
import { ProductCard } from "@point_of_sale/app/components/product_card/product_card";
import { wiseIsTracked } from "./stock_utils";

patch(ProductCard.prototype, {
    setup() {
        super.setup(...arguments);
        this.pos = usePos();
    },

    /** {value, colorClass, out} for the stock badge, or null when nothing should be shown. */
    get wiseStockBadge() {
        const pos = this.pos;
        const product = this.props.product;
        if (!pos?.config?.is_display_stock || this.props.isComboPopup || !product || !wiseIsTracked(product)) {
            return null;
        }
        if (!pos.wiseStockData?.loaded) {
            return null;
        }
        const isVariant = product.product_tmpl_id && product.product_tmpl_id !== product;
        const qty = isVariant ? pos.wiseProductQty(product) : pos.wiseTemplateQty(product);
        const value = qty - Number(this.props.productCartQty || 0);
        const threshold = pos.config.low_stock_threshold || 0;
        const color = value <= threshold ? pos.config.low_stock_color : pos.config.in_stock_color;
        return {
            value: Math.round(value * 100) / 100,
            colorClass: `o_colorlist_item_color_${color}`,
            out: pos.config.is_restrict_out_of_stock_products && value <= 0,
        };
    },
});
