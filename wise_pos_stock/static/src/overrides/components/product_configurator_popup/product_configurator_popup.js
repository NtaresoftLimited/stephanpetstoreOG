/** @odoo-module */
import { patch } from '@web/core/utils/patch';
import { ProductConfiguratorPopup } from '@point_of_sale/app/store/product_configurator_popup/product_configurator_popup';
import { getProductQty } from '@wise_pos_stock/utils';

patch(ProductConfiguratorPopup.prototype, {
    get variantStock() {
        const product = this.state.product;
        if (!product || product.type === 'service') {
            return null;
        }
        
        const qty = getProductQty(this.pos.config.stock_type, product);
        
        // Subtract quantity already in cart
        const orderlines = this.pos.selectedOrder?.orderlines || [];
        let cartQty = 0;
        for (const line of orderlines) {
            if (line.product.id === product.id) {
                cartQty += line.quantity;
            }
        }
            
        return qty - cartQty;
    },
    
    get stockColorClass() {
        const qty = this.variantStock;
        if (qty === null) return '';
        
        const threshold = this.pos.config.low_stock_threshold || 0;
        return qty <= threshold 
            ? `text-bg-${this.getBootstrapColor(this.pos.config.low_stock_color)}`
            : `text-bg-${this.getBootstrapColor(this.pos.config.in_stock_color)}`;
    },

    getBootstrapColor(odooColorIndex) {
        const mapping = {
            '1': 'danger',  // Red
            '10': 'success', // Green
            '3': 'warning', // Yellow
            '4': 'info',    // Blue
        };
        return mapping[odooColorIndex] || 'secondary';
    }
});
