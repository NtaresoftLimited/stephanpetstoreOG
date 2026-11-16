/** @odoo-module */
import { patch } from '@web/core/utils/patch';
import { _t } from '@web/core/l10n/translation';
import { getProductQty } from '../../utils';
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";

patch(PosOrderline.prototype, {
  set_quantity(quantity, keep_price) {
    const config = this.models?.["pos.config"]?.getFirst() || this.pos?.config;
    if (
      config?.is_restrict_out_of_stock_products &&
      this.product_id &&
      this.product_id.type !== "service"
    ) {
      const targetQty = Number(quantity || 0);
      const availableQty = getProductQty(config.stock_type, this.product_id);

      if (targetQty > availableQty) {
        if (this.env?.services?.notification) {
          this.env.services.notification.add(
            _t(`Insufficient Stock: "${this.product_id.display_name || this.product_id.name}" has only ${availableQty} available at this location.`),
            { type: "danger" }
          );
        }
        return false;
      }
    }
    return super.set_quantity(quantity, keep_price);
  },
});
