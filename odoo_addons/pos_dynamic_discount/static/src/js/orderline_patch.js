/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";

/**
 * Patch PosOrderline to track fixed discount amounts for display
 * This ensures the fixed_discount_amount is available in templates
 */
console.log("[POS Dynamic Discount] Loading Orderline Patch...");

patch(PosOrderline.prototype, {
    /**
     * Override init to initialize fixed discount tracking
     */
    init_from_JSON(json) {
        super.init_from_JSON(...arguments);
        // Restore fixed discount amount from saved data
        this.fixed_discount_amount = json.fixed_discount_amount || 0;
    },

    /**
     * Override export to save fixed discount amount
     */
    export_as_JSON() {
        const json = super.export_as_JSON(...arguments);
        json.fixed_discount_amount = this.fixed_discount_amount || 0;
        return json;
    },

    /**
     * Set a fixed amount discount on this order line
     * @param {number} amount - The fixed discount amount
     */
    setFixedDiscountAmount(amount) {
        this.fixed_discount_amount = Math.round(Math.abs(amount));
    },

    /**
     * Get the fixed discount amount for display
     * @returns {number} The fixed discount amount
     */
    getFixedDiscountAmount() {
        return this.fixed_discount_amount || 0;
    },

    /**
     * Check if this line has a fixed discount applied
     * @returns {boolean}
     */
    hasFixedDiscount() {
        return (this.fixed_discount_amount || 0) > 0;
    },
});

/**
 * Helper class for formatting discount display
 */
export class OrderLineDisplayHelper {
    static getDiscountInfo(line) {
        if (line.fixed_discount_amount && line.fixed_discount_amount > 0) {
            return `With a ${Math.round(line.fixed_discount_amount)} discount`;
        }
        const discount = line.get_discount ? line.get_discount() : line.discount;
        if (discount && discount > 0) {
            return `With a ${Math.round(discount * 100) / 100}% discount`;
        }
        return '';
    }
}
