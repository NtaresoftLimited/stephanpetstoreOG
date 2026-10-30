/** @odoo-module */
export function getProductQty(stockType, product) {
  const qty =
    stockType == 'on_hand' ? product.qty_available : product.virtual_available;
  return qty;
}

export function computeMarginInfo(product) {
  const cost = product.standard_price || 0;
  const sale = product.lst_price || product.list_price || 0;
  const marginAbs = sale - cost;
  const marginPercent = sale > 0 ? (marginAbs / sale) * 100 : 0;
  return { cost, sale, marginAbs, marginPercent };
}

export function checkMarginRestriction(product, config) {
  // Skip if margin restriction is disabled
  if (!config.is_restrict_low_margin_products) return null;

  // Check Product Type Configuration
  const checkType = config.margin_check_product_type || 'goods';
  const isService = product.type === 'service';

  if (checkType === 'goods' && isService) return null; // Skip services
  if (checkType === 'service' && !isService) return null; // Skip goods

  const { cost, sale, marginPercent } = computeMarginInfo(product);
  const threshold = config.margin_threshold_percent || 5;

  if (cost === 0) {
    return { blocked: true, reason: 'No purchase price defined' };
  }

  if (sale === 0) {
    return { blocked: true, reason: 'No sale price defined' };
  }

  if (marginPercent < 0) {
    return {
      blocked: true,
      reason: `Negative margin (Cost: ${cost.toFixed(2)}, Sale: ${sale.toFixed(2)})`
    };
  }

  if (marginPercent < threshold) {
    return {
      blocked: config.margin_restriction_level !== 'warn',
      reason: `Margin ${marginPercent.toFixed(1)}% below ${threshold}% threshold`
    };
  }

  return null; // No restriction
}
