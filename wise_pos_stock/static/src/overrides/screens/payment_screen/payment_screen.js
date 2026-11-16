/** @odoo-module */
import { patch } from '@web/core/utils/patch';
import { _t } from '@web/core/l10n/translation';
import { PaymentScreen } from '@point_of_sale/app/screens/payment_screen/payment_screen';
import { AlertDialog } from '@web/core/confirmation_dialog/confirmation_dialog';
import { getProductQty } from '../../../utils';

patch(PaymentScreen.prototype, {
  async validateOrder() {
    const currentOrder = this.pos.get_order() || this.currentOrder;
    const lines = (currentOrder && (currentOrder.get_orderlines?.() || currentOrder.lines)) || [];

    if (lines.length > 0 && this.pos.config.is_restrict_out_of_stock_products) {
      const outOfStockProducts = [];
      for (const line of lines) {
        const product = line.product || line.product_id;
        if (!product || product.type === 'service') continue;

        const availableQty = getProductQty(this.pos.config.stock_type, product);
        const requestedQty = Number(line.quantity ?? line.qty ?? 0);

        if (availableQty < requestedQty) {
          outOfStockProducts.push(`• ${product.display_name || product.name}: Available ${availableQty}, Requested ${requestedQty}`);
        }
      }

      if (outOfStockProducts.length > 0) {
        this.dialog.add(AlertDialog, {
          title: _t('Insufficient Stock'),
          body: _t(
            `The requested quantity exceeds available stock at this location:

${outOfStockProducts.join('\n')}

Please adjust the quantity before validating.`
          ),
        });
        return;
      }
    }
    return super.validateOrder(...arguments);
  },

  async _finalizeValidation() {
    const currentOrder = this.pos.get_order() || this.currentOrder;
    const lines = (currentOrder && (currentOrder.get_orderlines?.() || currentOrder.lines)) || [];

    for (const line of lines) {
      const product = line.product || line.product_id;
      if (!product || product.type === 'service') continue;

      const qty = Number(line.quantity ?? line.qty ?? 0);
      if (typeof product.qty_available === 'number' && !isNaN(product.qty_available)) {
        product.qty_available = Math.max(0, product.qty_available - qty);
      }
      if (typeof product.virtual_available === 'number' && !isNaN(product.virtual_available)) {
        product.virtual_available = Math.max(0, product.virtual_available - qty);
      }
    }

    return super._finalizeValidation(...arguments);
  },
});
