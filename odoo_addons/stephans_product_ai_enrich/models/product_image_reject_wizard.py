# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ProductImageRejectWizard(models.TransientModel):
    _name = "product.image.reject.wizard"
    _description = "Reject Image Asset Wizard"

    review_id = fields.Many2one(
        "product.image.review",
        string="Image Asset",
        required=True,
    )
    reason_code = fields.Selection(
        [
            ("watermark", "Visible Watermark / Retailer Logo / Promotional Overlay"),
            ("low_res", "Insufficient Resolution / Enlarged Blurry Thumbnail"),
            ("wrong_product", "Packaging Mismatch (Wrong Flavour, Life-stage, or Pack Weight)"),
            ("bad_aspect", "Irregular Aspect Ratio / Distorted Framing"),
            ("duplicate", "Duplicate of Existing Gallery Asset"),
            ("licensing", "Uncertain Provenance / Non-Manufacturer Source"),
            ("other", "Other Reason (Specify Below)"),
        ],
        string="Rejection Category",
        required=True,
        default="watermark",
    )
    rejection_notes = fields.Text(
        string="Detailed Rejection Notes",
        required=True,
        help="Mandatory explanation for audit compliance and provenance tracking.",
    )

    def action_confirm_rejection(self):
        self.ensure_one()
        review = self.review_id
        if review.approval_status != "pending_review":
            raise UserError(_("Only pending images can be rejected."))

        category_labels = dict(self._fields["reason_code"].selection)
        full_reason = f"[{category_labels.get(self.reason_code)}] {self.rejection_notes.strip()}"

        review.write({
            "approval_status": "rejected",
            "approved_by_id": self.env.uid,
            "approval_date": fields.Datetime.now(),
            "rejection_reason": full_reason,
            "raw_image": False,  # Purge raw binary on rejection to optimize filestore
        })
        review.product_tmpl_id._recompute_image_quality_status()
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Image Rejected"),
                "message": _("Image rejected and marked audit trail with reason."),
                "type": "warning",
                "sticky": False,
            },
        }
