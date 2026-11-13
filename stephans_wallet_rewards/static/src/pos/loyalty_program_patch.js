/** Paw Points in the POS: only customers with an active portal account (partner.paw_points_eligible)
 * earn or redeem loyalty points. Mirrors the server rule in pos.order._process_loyalty, which is the
 * one actually enforced; this keeps the screen, receipt and customer display consistent with it. */
import { patch } from "@web/core/utils/patch";
import { LoyaltyProgram } from "@pos_loyalty/app/models/loyalty_program";

function pawPointsBlocked(program, order) {
    return (
        program.program_type === "loyalty" &&
        !order.isRefund &&
        !order.partner_id?.paw_points_eligible
    );
}

patch(LoyaltyProgram.prototype, {
    getEarnedPoints(order) {
        return pawPointsBlocked(this, order) ? 0 : super.getEarnedPoints(...arguments);
    },
    getAvailablePoints(order) {
        return pawPointsBlocked(this, order) ? 0 : super.getAvailablePoints(...arguments);
    },
});
