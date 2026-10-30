/** @odoo-module */
import { patch } from '@web/core/utils/patch';
import { ProductScreen } from '@point_of_sale/app/screens/product_screen/product_screen';
import { getProductQty, checkMarginRestriction } from '@wise_pos_stock/utils';

patch(ProductScreen.prototype, {
  getCurrentOrderProductQty(productId) {
    const orderlines = this.pos.selectedOrder.orderlines || [];
    return orderlines
      .filter((line) => line.product.id === productId)
      .reduce((acc, line) => acc + line.get_quantity(), 0);
  },
  getClass(product) {
    let className = this.pos.productViewMode;

    // Stock restriction - disable out-of-stock products (except services)
    if (this.pos.config.is_restrict_out_of_stock_products) {
      let qty = getProductQty(this.pos.config.stock_type, product);
      qty = qty - this.getCurrentOrderProductQty(product.id);
      if (qty <= 0 && product.type !== 'service') {
        className += ' disabled';
      }
    }

    // Margin restriction - disable low-margin products
    if (this.pos.config.is_restrict_low_margin_products) {
      const marginCheck = checkMarginRestriction(product, this.pos.config);
      if (marginCheck?.blocked) {
        className += ' disabled';
      }
    }

    return className;
  },

  getProductLatestQty(product) {
    const lowStockThreshold = this.pos.config.low_stock_threshold || 0;
    let qty = getProductQty(this.pos.config.stock_type, product);
    let colorClass = '';
    qty = qty - this.getCurrentOrderProductQty(product.id);
    if (qty <= lowStockThreshold) {
      colorClass = `o_colorlist_item_color_${this.pos.config.low_stock_color}`;
    } else {
      colorClass = `o_colorlist_item_color_${this.pos.config.in_stock_color}`;
    }

    return { value: qty, colorClass: colorClass };
  },

  getProductType(product) {
    return product.type;
  },

});

