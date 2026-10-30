/** @odoo-module **/

import { patch } from "@web/core/utils/patch";

// Try to patch the OrderLine component from multiple possible paths
const possibleOrderLinePaths = [
    "@point_of_sale/app/generic_components/orderline/orderline",
    "@point_of_sale/app/screens/receipt_screen/receipt/orderline/orderline",
    "@point_of_sale/app/models/orderline"
];

// Function to try patching OrderLine from different paths
async function tryPatchOrderLine() {
    for (const path of possibleOrderLinePaths) {
        try {
            const module = await import(path);
            const OrderLine = module.Orderline || module.OrderLine || module.default;
            
            if (OrderLine) {
                console.log(`Successfully found OrderLine at ${path}`);
                
                // Patch the OrderLine component to show original price in unit price display
                patch(OrderLine.prototype, {
                    get_unit_price() {
                        const originalPrice = this.original_price || this._original_price_for_display;
                        if (originalPrice && this.discount > 0) {
                            // Return original price for display purposes
                            return originalPrice;
                        }
                        // Call the original method
                        return super.get_unit_price();
                    },
                    
                    get_display_unit_price() {
                        const originalPrice = this.original_price || this._original_price_for_display;
                        if (originalPrice && this.discount > 0) {
                            return originalPrice;
                        }
                        return this.get_unit_price();
                    }
                });
                
                return true;
            }
        } catch (error) {
            console.warn(`Could not import OrderLine from ${path}:`, error);
        }
    }
    return false;
}

// Try to patch OrderLine
tryPatchOrderLine().then(success => {
    if (success) {
        console.log("OrderLine patched successfully");
    } else {
        console.warn("Could not patch OrderLine from any path");
    }
});

// Alternative approach: Patch the OrderLine model directly
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";

patch(ControlButtons.prototype, {
    setup() {
        super.setup();
        // Override the unit price display in order lines
        this.enhanceOrderLineDisplay();
    },
    
    enhanceOrderLineDisplay() {
        // Monitor for changes in the order and update display
        const order = this.pos.get_order();
        if (order) {
            const lines = order.get_orderlines();
            lines.forEach(line => {
                if (line.discount > 0 && line.original_price) {
                    // Override the unit price display
                    line._display_unit_price = line.original_price;
                }
            });
        }
    }
});
