/** @odoo-module */
import { patch } from '@web/core/utils/patch';
import { ProductScreen } from '@point_of_sale/app/screens/product_screen/product_screen';
import { getProductQty, checkMarginRestriction } from '@wise_pos_stock/utils';

patch(ProductScreen.prototype, {
  getCurrentOrderProductQty(productId) {
    const orderlines = this.pos.selectedOrder?.orderlines || [];
    let total = 0;
    for (const line of orderlines) {
        if (line.product.id === productId) {
            total += line.quantity;
        }
    }
    return total;
  },
  getClass(product) {
    let className = this.pos.productViewMode || '';

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

  getProductTotalStock(product, stockType) {
    let totalStock = Number(getProductQty(stockType, product) || 0);

    // If this product represents a template with sibling variants, sum stock across variants
    const tmplId = Array.isArray(product.product_tmpl_id) ? product.product_tmpl_id[0] : product.product_tmpl_id;
    if (tmplId && this.pos.models && this.pos.models["product.product"]) {
      const allProducts = this.pos.models["product.product"].getAll?.() || [];
      for (const p of allProducts) {
        if (p.id !== product.id) {
          const pTmplId = Array.isArray(p.product_tmpl_id) ? p.product_tmpl_id[0] : p.product_tmpl_id;
          if (pTmplId === tmplId) {
            totalStock += Number(getProductQty(stockType, p) || 0);
          }
        }
      }
    }
    return totalStock;
  },

  get productsToDisplay() {
    let list = [];

    if (this.searchWord !== "") {
      list = this.addMainProductsToDisplay(this.getProductsBySearchWord(this.searchWord));
    } else if (this.pos.selectedCategory?.id) {
      list = this.getProductsByCategory(this.pos.selectedCategory);
    } else {
      list = this.products;
    }

    if (!list) {
      return [];
    }

    const onlyInStock = this.pos.config.only_in_stock_products !== false;
    const stockType = this.pos.config.stock_type || 'on_hand';

    const excludedIds = new Set([
      this.pos.config.tip_product_id?.id,
      ...(this.pos.hiddenProductIds || []),
      ...(this.pos.session?._pos_special_products_ids || []),
    ]);

    list = list.filter((product) => {
      if (!product.available_in_pos) {
        return false;
      }
      if (excludedIds.has(product.id)) {
        return false;
      }

      // Filter out of stock products (services are always kept)
      if (onlyInStock && product.type !== 'service') {
        const qty = this.getProductTotalStock(product, stockType);
        if (qty <= 0) {
          return false;
        }
      }

      return true;
    });

    if (this.searchWord === "") {
      list.sort((a, b) => (a.display_name || '').localeCompare(b.display_name || ''));
    }

    return list.slice(0, 100);
  },

});
