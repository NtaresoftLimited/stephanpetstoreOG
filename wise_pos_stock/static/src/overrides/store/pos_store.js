/** @odoo-module */
import { patch } from '@web/core/utils/patch';
import { PosStore } from '@point_of_sale/app/store/pos_store';
import { getProductQty, checkMarginRestriction } from '../../utils';
import { _t } from '@web/core/l10n/translation';

patch(PosStore.prototype, {
  async addLineToCurrentOrder(vals, opts = {}, isScale = false) {
    let product = vals?.product_id;
    if (vals && vals.id && (vals.display_name || vals.name)) {
      product = vals;
    }
    
    if (product && product.type !== 'service' && this.config.is_restrict_out_of_stock_products) {
      const availableQty = getProductQty(this.config.stock_type, product);
      const currentOrder = this.get_order();
      const currentLines = currentOrder?.get_orderlines?.() || currentOrder?.lines || [];
      let inCartQty = 0;
      for (const line of currentLines) {
        const lineProd = line.product || line.product_id;
        if (lineProd && lineProd.id === product.id) {
          inCartQty += Number(line.quantity ?? line.qty ?? 0);
        }
      }

      if (availableQty <= inCartQty) {
        this.notification.add(
          _t(`Insufficient Stock: "${product.display_name || product.name}" has only ${availableQty} available at this location.`),
          { type: 'danger' }
        );
        return;
      }
    }

    // Margin restriction check
    if (product) {
      const marginCheck = checkMarginRestriction(product, this.config);
      if (marginCheck) {
        if (marginCheck.blocked) {
          this.notification.add(_t('Margin Restriction: ') + marginCheck.reason, {
            type: 'danger',
          });
          return;
        } else {
          this.notification.add(_t('Warning: ') + marginCheck.reason, {
            type: 'warning',
          });
        }
      }
    }

    return super.addLineToCurrentOrder(vals, opts, isScale);
  },

  async addProductToCurrentOrder(product, options = {}) {
    if (product && product.type !== 'service' && this.config.is_restrict_out_of_stock_products) {
      const availableQty = getProductQty(this.config.stock_type, product);
      const currentOrder = this.get_order();
      const currentLines = currentOrder?.get_orderlines?.() || currentOrder?.lines || [];
      let inCartQty = 0;
      for (const line of currentLines) {
        const lineProd = line.product || line.product_id;
        if (lineProd && lineProd.id === product.id) {
          inCartQty += Number(line.quantity ?? line.qty ?? 0);
        }
      }

      if (availableQty <= inCartQty) {
        this.notification.add(
          _t(`Insufficient Stock: "${product.display_name || product.name}" has only ${availableQty} available at this location.`),
          { type: 'danger' }
        );
        return;
      }
    }

    // Margin restriction check
    if (product) {
      const marginCheck = checkMarginRestriction(product, this.config);
      if (marginCheck) {
        if (marginCheck.blocked) {
          this.notification.add(_t('Margin Restriction: ') + marginCheck.reason, {
            type: 'danger',
          });
          return;
        } else {
          this.notification.add(_t('Warning: ') + marginCheck.reason, {
            type: 'warning',
          });
        }
      }
    }

    return super.addProductToCurrentOrder(product, options);
  },

  async pay() {
    const currentOrder = this.get_order();
    const orderLines = currentOrder?.get_orderlines?.() || currentOrder?.lines || [];

    // Check stock availability
    if (this.config.is_restrict_out_of_stock_products) {
      const outOfStockProducts = [];
      for (const line of orderLines) {
        const product = line.product || line.product_id;
        if (!product || product.type === 'service') continue;

        const availableQty = getProductQty(this.config.stock_type, product);
        const requestedQty = Number(line.quantity ?? line.qty ?? 0);
        if (availableQty < requestedQty) {
          outOfStockProducts.push(`"${product.display_name || product.name}" (Stock: ${availableQty}, Ordered: ${requestedQty})`);
        }
      }

      if (outOfStockProducts.length > 0) {
        this.notification.add(
          _t('Insufficient Stock: ') + outOfStockProducts.join(', '),
          { type: 'danger' }
        );
        return;
      }
    }

    // Check margin violations
    if (this.config.is_restrict_low_margin_products) {
      const marginViolations = [];
      for (const line of orderLines) {
        const product = line.product || line.product_id;
        if (!product) continue;

        const marginCheck = checkMarginRestriction(product, this.config);
        if (marginCheck?.blocked) {
          marginViolations.push(`${product.display_name || product.name}: ${marginCheck.reason}`);
        }
      }

      if (marginViolations.length > 0) {
        this.notification.add(
          _t('Margin Restriction: ') + marginViolations.join(', '),
          { type: 'danger' }
        );
        return;
      }
    }

    return super.pay(...arguments);
  },
});
