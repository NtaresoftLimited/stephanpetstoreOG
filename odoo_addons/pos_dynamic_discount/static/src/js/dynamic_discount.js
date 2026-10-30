/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { NumberPopup } from "@point_of_sale/app/utils/input_popups/number_popup";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";

patch(ControlButtons.prototype, {
    setup() {
        super.setup(...arguments);
    },

    async discountPopup(discount_type) {
        var self = this;

        this.dialog.add(NumberPopup, {
            title: _t("Discount"),
            startingValue: 0, // Start with 0 for both types
            getPayload: (num) => {
                const val = Math.max(
                    0,
                    Math.min(1000000, this.env.utils.parseValidFloat(num.toString())) // Increased limit for fixed amounts
                );
                self.apply_discount(val, discount_type);
            },
        });
    },

    async clickDiscount() {
        const self = this;

        const discount_type = await new Promise((resolve) => {
            this.dialog.add(ConfirmationDialog, {
                title: _t('Select Discount Type'),
                body: _t(
                    'Please select the applied global discount type.'
                ),
                confirm: () => {
                    resolve('percentage');
                },
                cancel: () => {
                    resolve('amount');
                },
                confirmLabel: _t('Percentage'),
                cancelLabel: _t('Amount'),
            });
        });

        await this.discountPopup(discount_type);
    },

    async apply_discount(pc, discount_type) {
        const order = this.pos.get_order();
        const lines = order.get_orderlines();
        const product = this.pos.config.discount_product_id;

        if (product === undefined) {
            this.dialog.add(AlertDialog, {
                title: _t("No discount product found"),
                body: _t(
                    "The discount product seems misconfigured. Make sure it is flagged as 'Can be Sold' and 'Available in Point of Sale'."
                ),
            });
            return;
        }

        // Remove existing discounts
        lines.filter((line) => line.get_product() === product).forEach((line) => line.delete());

        // Get discount limits from POS config, with defaults (100% and 1,000,000)
        // Fixed: Use value directly without multiplying by 100
        const maxPercentageDiscount = this.pos.config.max_percentage_discount || 100.0;
        const maxFixedAmountDiscount = this.pos.config.max_fixed_amount_discount || 1000000;

        // Validate discount limits
        if (discount_type === 'percentage' && pc > maxPercentageDiscount) {
            this.dialog.add(AlertDialog, {
                title: _t("Discount Limit Exceeded"),
                body: _t(
                    "The maximum percentage discount allowed is %s%%. Please enter a lower value.",
                    maxPercentageDiscount
                ),
            });
            return;
        }

        if (discount_type === 'amount' && pc > maxFixedAmountDiscount) {
            this.dialog.add(AlertDialog, {
                title: _t("Discount Limit Exceeded"),
                body: _t(
                    "The maximum fixed amount discount allowed is %s. Please enter a lower value.",
                    this.env.utils.formatCurrency(maxFixedAmountDiscount)
                ),
            });
            return;
        }

        // Get all lines that are applicable for discount (not discount products themselves)
        const applicableLines = lines.filter((line) => line.isGlobalDiscountApplicable());

        if (applicableLines.length === 0) {
            this.dialog.add(AlertDialog, {
                title: _t("No Products to Discount"),
                body: _t("There are no products in the order that can be discounted."),
            });
            return;
        }

        // Apply discounts within each product line for all cases
        await this.applyDiscountWithinProducts(applicableLines, pc, discount_type);
    },

    async applyDiscountWithinProducts(applicableLines, pc, discount_type) {
        // Apply discount using standard Odoo mechanism
        for (const line of applicableLines) {
            // Get the original product price
            const product = line.get_product();
            const originalPrice = product.lst_price;

            // Calculate discount percentage
            let discountPercentage = 0;
            let fixedDiscountPerLine = 0;

            if (discount_type === 'amount') {
                // For fixed amount, calculate equivalent percentage for each product
                fixedDiscountPerLine = Math.abs(pc) / applicableLines.length;
                discountPercentage = (fixedDiscountPerLine / originalPrice) * 100;

                // Round to 2 decimal places
                discountPercentage = Math.round(discountPercentage * 100) / 100;

                // Store the fixed discount amount for display
                if (line.setFixedDiscountAmount) {
                    line.setFixedDiscountAmount(fixedDiscountPerLine);
                } else {
                    line.fixed_discount_amount = fixedDiscountPerLine;
                }
            } else {
                // For percentage, use directly
                discountPercentage = pc;
                // Clear any fixed discount amount
                if (line.setFixedDiscountAmount) {
                    line.setFixedDiscountAmount(0);
                } else {
                    line.fixed_discount_amount = 0;
                }
            }

            // Store original price information for display purposes
            line.original_price = originalPrice;
            line.discount_applied = discountPercentage;

            // Set the original price as the unit price for display
            line.set_unit_price(originalPrice);

            // Apply the discount using standard Odoo mechanism
            line.set_discount(Math.min(discountPercentage, 100));

            // Store the original price for display purposes
            line._original_price_for_display = originalPrice;

            // Override the unit price display to show original price
            line._display_unit_price = originalPrice;

            // Add a custom method to get the display unit price
            line.get_display_unit_price = function () {
                return this.original_price || this._original_price_for_display || this.get_unit_price();
            };
        }
    },

    async applyGlobalDiscount(applicableLines, pc, discount_type, discountProduct, order) {
        if (discount_type === 'amount') {
            // Fixed Amount Discount - Apply the full fixed amount as specified
            let lineConfig = {
                product_id: discountProduct,
                price_unit: -Math.abs(pc) // Negative for discount
            };

            // Try to get tax information from the first applicable line
            try {
                const firstLineTaxes = applicableLines[0].get_taxes();
                if (firstLineTaxes && firstLineTaxes.length > 0) {
                    const taxes = firstLineTaxes
                        .map((tax) => {
                            try {
                                const taxModel = this.pos.models["account.tax"];
                                return taxModel ? taxModel.get(tax.id) : tax;
                            } catch (e) {
                                return tax;
                            }
                        })
                        .filter(tax => tax !== null && tax !== undefined);

                    if (taxes.length > 0) {
                        lineConfig.tax_ids = [["link", ...taxes]];
                    }
                }
            } catch (e) {
                console.warn("Could not determine tax information for fixed amount discount:", e);
            }

            await this.pos.addLineToCurrentOrder(lineConfig, { merge: false });
        } else {
            // Percentage Discount - Apply percentage to order
            let baseToDiscount = 0;
            try {
                baseToDiscount = order.calculate_base_amount(applicableLines);
            } catch (error) {
                console.warn("Error calculating base amount, using fallback:", error);
                baseToDiscount = applicableLines.reduce((sum, line) => sum + (line.get_price_without_tax() || 0), 0);
            }

            const discount = (-pc / 100.0) * baseToDiscount;

            // Check if discount exceeds the base amount (over 100%)
            if (Math.abs(discount) > baseToDiscount) {
                this.dialog.add(AlertDialog, {
                    title: _t("Discount Exceeds Total"),
                    body: _t(
                        "The discount amount exceeds the order total. Please enter a lower value."
                    ),
                });
                return;
            }

            if (discount < 0) {
                let lineConfig = {
                    product_id: discountProduct,
                    price_unit: discount
                };

                // Try to get tax information for percentage discount
                try {
                    const firstLineTaxes = applicableLines[0].get_taxes();
                    if (firstLineTaxes && firstLineTaxes.length > 0) {
                        const taxes = firstLineTaxes
                            .map((tax) => {
                                try {
                                    const taxModel = this.pos.models["account.tax"];
                                    return taxModel ? taxModel.get(tax.id) : tax;
                                } catch (e) {
                                    return tax;
                                }
                            })
                            .filter(tax => tax !== null && tax !== undefined);

                        if (taxes.length > 0) {
                            lineConfig.tax_ids = [["link", ...taxes]];
                        }
                    }
                } catch (e) {
                    console.warn("Could not determine tax information for percentage discount:", e);
                }

                await this.pos.addLineToCurrentOrder(lineConfig, { merge: false });
            }
        }
    },
});

// Enhanced discount display functionality
// This will be handled through the existing discount application logic