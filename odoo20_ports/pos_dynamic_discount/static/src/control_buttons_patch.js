import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
// Load pos_discount's patch first: our applyDiscount wraps the one it adds.
import "@pos_discount/app/screens/product_screen/control_buttons/control_buttons";

/**
 * Enforce the per-till discount limits (Odoo 18 pos_dynamic_discount) on Odoo 20's own
 * global discount button. Only the cashier's entry is checked: the standard code re-applies
 * an accepted discount by itself whenever the order changes.
 */
patch(ControlButtons.prototype, {
    async applyDiscount(value, type) {
        const config = this.pos.config;
        const alert = (title, body) => this.dialog.add(AlertDialog, { title, body });

        if (type === "percent") {
            const max = config.max_percentage_discount || 0;
            if (max > 0 && value > max) {
                alert(
                    _t("Discount Limit Exceeded"),
                    _t("The maximum percentage discount allowed is %s%%. Please enter a lower value.", max)
                );
                return;
            }
        } else if (type === "fixed") {
            const max = config.max_fixed_amount_discount || 0;
            if (max > 0 && value > max) {
                alert(
                    _t("Discount Limit Exceeded"),
                    _t(
                        "The maximum fixed amount discount allowed is %s. Please enter a lower value.",
                        this.pos.formatCurrency(max)
                    )
                );
                return;
            }
            const order = this.pos.getOrder();
            const base = (order?.getOrderlines() || [])
                .filter((line) => line.isGlobalDiscountApplicable())
                .reduce((sum, line) => sum + line.priceIncl, 0);
            if (value > Math.abs(base) + 0.0001) {
                alert(
                    _t("Discount Exceeds Total"),
                    _t("The discount (%s) is more than the order total (%s). Please enter a lower value.",
                        this.pos.formatCurrency(value), this.pos.formatCurrency(Math.abs(base)))
                );
                return;
            }
        }
        return super.applyDiscount(...arguments);
    },
});
