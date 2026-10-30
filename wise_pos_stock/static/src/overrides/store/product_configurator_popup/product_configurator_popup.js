/** @odoo-module */
import { patch } from '@web/core/utils/patch';
import { ProductConfiguratorPopup } from '@point_of_sale/app/store/product_configurator_popup/product_configurator_popup';
import { getProductQty } from '@wise_pos_stock/utils';

patch(ProductConfiguratorPopup.prototype, {
    getProductLatestQty(product) {
        if (!product) {
            return { value: 0, colorClass: '' };
        }
        const lowStockThreshold = this.pos.config.low_stock_threshold || 0;
        let qty = getProductQty(this.pos.config.stock_type, product);
        
        // Aggregate quantity from current order
        const orderlines = this.pos.selectedOrder?.orderlines || [];
        const orderQty = orderlines
            .filter((line) => line.product.id === product.id)
            .reduce((acc, line) => acc + line.get_quantity(), 0);
            
        qty = qty - orderQty;
        
        let colorClass = '';
        if (qty <= lowStockThreshold) {
            colorClass = `o_colorlist_item_color_${this.pos.config.low_stock_color}`;
        } else {
            colorClass = `o_colorlist_item_color_${this.pos.config.in_stock_color}`;
        }

        return { value: qty, colorClass: colorClass };
    },
});
