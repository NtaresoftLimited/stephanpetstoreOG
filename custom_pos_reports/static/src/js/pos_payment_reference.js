/** @odoo-module */
/**
 * custom_pos_reports/pos_payment_reference.js
 *
 * NOTE: The main PaymentScreen payment reference enforcement logic
 * (validateOrder, addNewPaymentLine, requiresRef, editPaymentRef)
 * lives in techovers_business_suite/static/src/js/pos_payment_reference.js
 *
 * This file is kept minimal to avoid duplicate patches.
 * It only handles the POS receipt data enrichment for the
 * payment reference field in the receipt screen props.
 */

// All logic consolidated in techovers_business_suite module.
// This stub prevents double-patching.
