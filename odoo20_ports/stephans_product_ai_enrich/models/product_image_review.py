# -*- coding: utf-8 -*-
import base64
import hashlib
import io
import logging
from PIL import Image

from odoo import api, fields, models, _
from odoo.exceptions import UserError

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
    source_type = fields.Selection(
        [
            ("manufacturer", "Official Manufacturer Catalogue"),
            ("distributor", "Authorized Distributor"),
            ("internal", "Stephan's Internal Photography"),
            ("licensed", "Explicitly Licensed Reuse"),
        ],
        string="Source Type",
        default="manufacturer",
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
    file_checksum = fields.Char(
        string="File SHA-256 Checksum",
        readonly=True,
        index=True,
    )
    usage_license_note = fields.Char(
        string="Usage / License Note",
        default="Authorized distribution packshot",
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

    def action_approve_and_publish(self):
        """Human approval action: publishes clean WebP / raw derivative directly to eCommerce catalog."""
        self.ensure_one()
        product = self.product_tmpl_id
        img_data = self.webp_image or self.raw_image
        if not img_data:
            raise UserError(_("No image binary available to publish."))

        now = fields.Datetime.now()
        if self.image_role == "front" or not product.image_1920:
            product.sudo().write({"image_1920": img_data})
        else:
            # Add to secondary gallery images
            self.env["product.image"].sudo().create({
                "name": self.name,
                "product_tmpl_id": product.id,
                "image_1920": img_data,
            })

        self.write({
            "approval_status": "approved",
            "approved_by_id": self.env.uid,
            "approval_date": now,
            "rejection_reason": False,
        })
        product.sudo().write({"image_quality_status": "approved"})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Image Approved & Published"),
                "message": _("Image published cleanly to %s storefront gallery.", product.display_name),
                "type": "success",
                "sticky": False,
            },
        }

    def action_reject(self):
        """Reject image with reason."""
        self.ensure_one()
        self.write({
            "approval_status": "rejected",
            "approved_by_id": self.env.uid,
            "approval_date": fields.Datetime.now(),
        })
        # Check if all images for this product are rejected
        other_active = self.search([
            ("product_tmpl_id", "=", self.product_tmpl_id.id),
            ("id", "!=", self.id),
            ("approval_status", "=", "approved"),
        ], limit=1)
        if not other_active:
            self.product_tmpl_id.sudo().write({"image_quality_status": "rejected"})
