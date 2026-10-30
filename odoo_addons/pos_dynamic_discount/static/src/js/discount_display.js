/** @odoo-module **/

// Enhanced discount display functionality
// This module provides utility functions for displaying discount information
// without requiring complex component patching

export class DiscountDisplayHelper {
    static getOrderlineDisplayInfo(line) {
        const product = line.get_product();
        const originalPrice = product.lst_price;
        const discount = line.get_discount();
        const quantity = line.get_quantity();
        const unitPrice = line.get_unit_price();
        const totalPrice = line.get_price_with_tax();
        
        // If there's a discount, show the enhanced format
        if (discount > 0) {
            const discountPercentage = Math.round(discount * 100) / 100;
            
            return {
                productName: product.display_name,
                originalPrice: originalPrice,
                discountedPrice: unitPrice,
                discountPercentage: discountPercentage,
                quantity: quantity,
                totalPrice: totalPrice,
                hasDiscount: true
            };
        }
        
        // Default format for non-discounted items
        return {
            productName: product.display_name,
            originalPrice: originalPrice,
            discountedPrice: unitPrice,
            discountPercentage: 0,
            quantity: quantity,
            totalPrice: totalPrice,
            hasDiscount: false
        };
    }
    
    static formatDiscountInfo(displayInfo) {
        if (displayInfo.hasDiscount) {
            return `(Discounted: ${displayInfo.discountedPrice} - ${displayInfo.discountPercentage}% off)`;
        }
        return '';
    }
}
