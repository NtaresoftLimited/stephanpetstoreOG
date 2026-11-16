// Shared helpers for wise_pos_stock (Odoo 20).

/** The POS store, set once data is loaded, so order-line models can read stock. */
export const wiseStock = { pos: null };

export function wiseTemplate(record) {
    // product.product -> its template; product.template -> itself
    return record?.product_tmpl_id || record;
}

/** Only storable goods are counted; services and non-tracked products are never limited. */
export function wiseIsTracked(record) {
    const tmpl = wiseTemplate(record);
    return Boolean(tmpl && tmpl.is_storable && tmpl.type !== "service");
}

export function computeMarginInfo(tmpl) {
    const cost = tmpl.standard_price || 0;
    const sale = tmpl.list_price || 0;
    const marginPercent = sale > 0 ? ((sale - cost) / sale) * 100 : 0;
    return { cost, sale, marginPercent };
}

/** Same rules as the Odoo 18 module: returns null or {blocked, reason}. */
export function checkMarginRestriction(record, config) {
    if (!config.is_restrict_low_margin_products) {
        return null;
    }
    const tmpl = wiseTemplate(record);
    const checkType = config.margin_check_product_type || "goods";
    const isService = tmpl.type === "service";
    if ((checkType === "goods" && isService) || (checkType === "service" && !isService)) {
        return null;
    }
    const { cost, sale, marginPercent } = computeMarginInfo(tmpl);
    const threshold = config.margin_threshold_percent || 5;
    if (!cost) {
        return { blocked: true, reason: "No purchase price defined" };
    }
    if (!sale) {
        return { blocked: true, reason: "No sale price defined" };
    }
    if (marginPercent < threshold) {
        return {
            blocked: config.margin_restriction_level !== "warn",
            reason: `Margin ${marginPercent.toFixed(1)}% below ${threshold}% threshold`,
        };
    }
    return null;
}
