/** @odoo-module */
import { patch } from '@web/core/utils/patch';
import { PosStore } from '@point_of_sale/app/store/pos_store';
import { getProductQty, checkMarginRestriction } from '../../utils';
import { _t } from '@web/core/l10n/translation';


patch(PosStore.prototype, {
  async addProductToCurrentOrder(product, options = {}) {
    // Stock restriction - exempt service products
    if (this.config.is_restrict_out_of_stock_products && product.type !== 'service') {
      const productQty = getProductQty(this.config.stock_type, product);
      if (productQty <= 0) {
        return;
      }
    }

    // Margin restriction check
    const marginCheck = checkMarginRestriction(product, this.config);
    if (marginCheck) {
      if (marginCheck.blocked) {
        this.notification.add(_t('Margin Restriction: ') + marginCheck.reason, {
          type: 'danger',
        });
        return;
      } else {
        // Warning only - allow sale
        this.notification.add(_t('Warning: ') + marginCheck.reason, {
          type: 'warning',
        });
      }
    }

    super.addProductToCurrentOrder(product, options);
  },

  async pay() {
    const currentOrder = this.get_order();
    const orderLines = currentOrder?.get_orderlines?.() || currentOrder || [];

    // Check stock availability
    if (this.config.is_restrict_out_of_stock_products) {
      const outOfStockProducts = [];
      for (const line of orderLines) {
        const product = line.product || line.product_id;
        if (!product || product.type === 'service') continue;

        const qty = getProductQty(this.config.stock_type, product);
        if (qty < (line.quantity || line.qty || 0)) {
          outOfStockProducts.push(product.display_name || product.name);
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

