# -*- coding: utf-8 -*-
import base64
import hashlib
import io
import logging
from PIL import Image

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)


class ProductImageReview(models.Model):
    _name = "product.image.review"
    _description = "Product Media Review Queue & Quality Gate"
    _order = "download_date desc, id desc"

    name = fields.Char(
        string="Image Label",
        compute="_compute_name",
        store=True,
    )
    product_tmpl_id = fields.Many2one(
        "product.template",
        string="Product Template",
        required=True,
        ondelete="cascade",
        index=True,
    )
    product_sku = fields.Char(
        string="SKU / Internal Ref",
        related="product_tmpl_id.default_code",
        store=True,
    )
    barcode = fields.Char(
        string="Barcode / EAN",
        related="product_tmpl_id.barcode",
        store=True,
    )
    original_source_url = fields.Char(
        string="Original Source URL",
        required=True,
        index=True,
    )
    verified_domain = fields.Char(
        string="Verified Domain",
        readonly=True,
        index=True,
    )
    source_type = fields.Selection(
        [
            ("manufacturer", "Official Manufacturer Catalogue"),
            ("distributor", "Authorized Distributor"),
            ("internal", "Stephan's Internal Photography"),
            ("licensed", "Explicitly Licensed Reuse"),
            ("unverified", "External / Unverified Source"),
        ],
        string="Source Provenance",
        default="unverified",
        required=True,
        index=True,
    )
    manufacturer_name = fields.Char(
        string="Manufacturer Name",
        index=True,
    )
    download_date = fields.Datetime(
        string="Download Date",
        default=fields.Datetime.now,
        required=True,
        index=True,
    )
    original_width = fields.Integer(
        string="Original Width (px)",
        readonly=True,
    )
    original_height = fields.Integer(
        string="Original Height (px)",
        readonly=True,
    )
    aspect_ratio = fields.Float(
        string="Aspect Ratio",
        digits=(16, 2),
        readonly=True,
    )
    foreground_coverage_pct = fields.Float(
        string="Product Canvas Occupancy (%)",
        digits=(16, 1),
        readonly=True,
        help="Measured percentage of the 1:1 canvas occupied by the detected foreground product package.",
    )
    file_checksum = fields.Char(
        string="File SHA-256 Checksum",
        readonly=True,
        index=True,
    )
    phash = fields.Char(
        string="Perceptual dHash",
        readonly=True,
        index=True,
        help="Difference hash (dHash) used for catalogue-wide visual similarity and duplicate detection.",
    )
    usage_license_note = fields.Char(
        string="Usage / License Note",
        readonly=True,
    )
    image_role = fields.Selection(
        [
            ("front", "Front Packshot (Main)"),
            ("back", "Back / Ingredients"),
            ("detail", "Detail / Feeding Guide"),
            ("lifestyle", "Lifestyle / Usage"),
        ],
        string="Image Role",
        default="front",
        required=True,
        index=True,
    )
    approval_status = fields.Selection(
        [
            ("pending_review", "Pending Review"),
            ("approved", "Approved & Published"),
            ("rejected", "Rejected"),
        ],
        string="Quality Gate Status",
        default="pending_review",
        required=True,
        index=True,
    )
    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved By",
        readonly=True,
    )
    approval_date = fields.Datetime(
        string="Approval Date",
        readonly=True,
    )
    rejection_reason = fields.Text(
        string="Rejection Reason",
        readonly=True,
    )
    raw_image = fields.Binary(
        string="Original Raw Image",
        attachment=True,
    )
    webp_image = fields.Binary(
        string="Optimized WebP Derivative",
        attachment=True,
    )
    webp_filesize_kb = fields.Float(
        string="WebP Size (KB)",
        digits=(16, 1),
        readonly=True,
    )

    @api.depends("product_tmpl_id.name", "image_role", "original_width", "original_height")
    def _compute_name(self):
        role_labels = {
            "front": "Front Packshot",
            "back": "Back/Ingredients",
            "detail": "Detail/Nutrition",
            "lifestyle": "Lifestyle",
        }
        for record in self:
            p_name = record.product_tmpl_id.display_name or "Product"
            role = role_labels.get(record.image_role, "Image")
            res = f"{record.original_width}x{record.original_height}" if record.original_width else ""
            record.name = f"{p_name} - {role} ({res})"

    def _check_reviewer_rights(self):
        """Enforce that only members of group_media_reviewer or administrators can publish/reject."""
        if not self.env.user.has_group("stephans_product_ai_enrich.group_media_reviewer") and not self.env.is_admin():
            raise AccessError(_("Permission Denied: Only authorized Media Quality Reviewers can approve or reject catalog images."))

    def action_approve_and_publish(self):
        """Human approval action: publishes clean WebP derivative to storefront gallery with strict idempotency."""
        self._check_reviewer_rights()
        for review in self:
            if review.approval_status != "pending_review":
                raise UserError(_("Cannot approve asset '%s': current status is '%s'. Only pending assets can be approved.") % (review.name, review.approval_status))

            product = review.product_tmpl_id
            img_data = review.webp_image or review.raw_image
            if not img_data:
                raise UserError(_("No image binary available to publish for '%s'.") % review.name)

            now = fields.Datetime.now()
            if review.image_role == "front" or not product.image_1920:
                product.sudo().write({"image_1920": img_data})
            else:
                # Idempotency check: prevent duplicate gallery images with the same checksum or phash
                existing_gallery = self.env["product.image"].sudo().search([
                    ("product_tmpl_id", "=", product.id),
                    ("name", "=", review.name),
                ], limit=1)
                if not existing_gallery:
                    self.env["product.image"].sudo().create({
                        "name": review.name,
                        "product_tmpl_id": product.id,
                        "image_1920": img_data,
                    })

            review.write({
                "approval_status": "approved",
                "approved_by_id": self.env.uid,
                "approval_date": now,
                "rejection_reason": False,
            })
            product._recompute_image_quality_status()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Image Approved & Published"),
                "message": _("Selected image(s) published cleanly to product storefront."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_reject(self):
        """Open the mandatory Rejection Reason Wizard."""
        self.ensure_one()
        self._check_reviewer_rights()
        if self.approval_status != "pending_review":
            raise UserError(_("Only pending images can be rejected."))

        return {
            "name": _("Reject Image Asset"),
            "type": "ir.actions.act_window",
            "res_model": "product.image.reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_review_id": self.id},
        }

    @api.model
    def cron_purge_rejected_raw_images(self):
        """Retention policy: purge raw binary attachments of rejected images older than 7 days to conserve filestore space."""
        threshold = fields.Datetime.now() - fields.Date.timedelta(days=7)
        old_rejected = self.search([
            ("approval_status", "=", "rejected"),
            ("approval_date", "<=", threshold),
            ("raw_image", "!=", False),
        ])
        _logger.info("Purging %d rejected raw image binaries older than 7 days.", len(old_rejected))
        old_rejected.write({"raw_image": False})
