# -*- coding: utf-8 -*-
import base64
import hashlib
import io
import logging
import math
from PIL import Image

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)

ELIGIBLE_APPROVAL_SOURCE_TYPES = frozenset({
    "manufacturer",
    "authorized_distributor",
    "distributor",
    "internal",
    "licensed",
})


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
            ("manufacturer", "Official Manufacturer Catalogue (Tier 1)"),
            ("authorized_distributor", "Authorized Distributor (Tier 1)"),
            ("trusted_retailer", "Trusted International Retailer (Tier 2 - Cross-Check Only)"),
            ("external_unverified", "External / Unverified Source"),
            # Legacy compatibility values
            ("distributor", "Authorized Distributor (Legacy)"),
            ("internal", "Stephan's Internal Photography"),
            ("licensed", "Explicitly Licensed Reuse"),
            ("unverified", "External / Unverified Source (Legacy)"),
        ],
        string="Source Provenance",
        default="external_unverified",
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
    dhash = fields.Char(
        string="Gradient dHash",
        readonly=True,
        index=True,
        help="64-bit gradient difference hash (dHash) in 16-hex format.",
    )
    phash = fields.Char(
        string="DCT pHash",
        readonly=True,
        index=True,
        help="64-bit Discrete Cosine Transform perceptual hash (pHash) in 16-hex format.",
    )
    gate1_status = fields.Selection(
        [
            ("pass", "Pass"),
            ("fail", "Fail"),
            ("identity_required", "Identity Required"),
        ],
        string="Gate 1: Exact Identity",
        readonly=True,
        index=True,
    )
    gate1_evidence = fields.Text(
        string="Gate 1 Evidence",
        readonly=True,
    )
    gate2_status = fields.Selection(
        [
            ("pass", "Pass"),
            ("fail", "Fail"),
        ],
        string="Gate 2: Source Provenance",
        readonly=True,
        index=True,
    )
    gate2_evidence = fields.Text(
        string="Gate 2 Evidence",
        readonly=True,
    )
    gate3_status = fields.Selection(
        [
            ("pass", "Pass"),
            ("fail", "Fail"),
        ],
        string="Gate 3: Quality & Cleanliness",
        readonly=True,
        index=True,
    )
    gate3_evidence = fields.Text(
        string="Gate 3 Evidence",
        readonly=True,
    )
    duplicate_comparison_summary = fields.Text(
        string="Duplicate Comparison Results",
        readonly=True,
    )
    view_role_evidence = fields.Char(
        string="View Role Evidence",
        readonly=True,
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
        string="Original High-Res Source (Gallery Zoom)",
        attachment=True,
    )
    webp_image = fields.Binary(
        string="Product-Page Preview (1200px WebP)",
        attachment=True,
    )
    webp_filesize_kb = fields.Float(
        string="Preview WebP Size (KB)",
        digits=(16, 1),
        readonly=True,
    )
    webp_card_480 = fields.Binary(
        string="Product-Card Derivative (480x480 WebP)",
        attachment=True,
    )
    webp_card_480_kb = fields.Float(
        string="Card 480px Size (KB)",
        digits=(16, 1),
        readonly=True,
    )
    webp_thumb_160 = fields.Binary(
        string="Search Thumbnail Derivative (160x160 WebP)",
        attachment=True,
    )
    webp_thumb_160_kb = fields.Float(
        string="Thumb 160px Size (KB)",
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

    @staticmethod
    def _normalize_image_binary(data):
        if not data:
            return b""
        raw = bytes(data)
        try:
            decoded = base64.b64decode(raw, validate=True)
            if len(decoded) > 10 and (decoded[:2] == b'\xff\xd8' or decoded[:4] == b'\x89PNG' or decoded[:4] == b'RIFF' or decoded[:3] == b'GIF'):
                return decoded
        except Exception:
            pass
        return raw

    @staticmethod
    def _compute_dct_phash(im):
        """Compute standard 64-bit DCT perceptual hash (pHash) without external dependencies."""
        try:
            gray = im.convert('L').resize((32, 32), Image.Resampling.LANCZOS)
            pixels = list(gray.getdata())
            cos_table = [[math.cos((2 * x + 1) * u * math.pi / 64.0) for x in range(32)] for u in range(8)]
            row_dct = []
            for r in range(32):
                row_pix = pixels[r * 32 : (r + 1) * 32]
                row_coeffs = [sum(row_pix[x] * cos_table[u][x] for x in range(32)) for u in range(8)]
                row_dct.append(row_coeffs)
            dct = []
            for u in range(8):
                for v in range(8):
                    dct.append(sum(row_dct[y][v] * cos_table[u][y] for y in range(32)))
            low_freq = dct[1:]
            sorted_coeffs = sorted(low_freq)
            median = (sorted_coeffs[31] + sorted_coeffs[32]) / 2.0
            bits = [1 if c > median else 0 for c in dct]
            return sum(b << i for i, b in enumerate(bits))
        except Exception:
            return None

    @classmethod
    def _extract_image_fingerprint(cls, data):
        normalized = cls._normalize_image_binary(data)
        if not normalized:
            return None, None, None
        sha256 = hashlib.sha256(normalized).hexdigest()
        try:
            im = Image.open(io.BytesIO(normalized))
            # dHash
            gray = im.convert('L').resize((9, 8), Image.Resampling.LANCZOS)
            pixels = list(gray.getdata())
            diff = [pixels[r * 9 + c] > pixels[r * 9 + c + 1] for r in range(8) for c in range(8)]
            dhash = sum(1 << i for i, v in enumerate(diff) if v)
            # pHash
            phash = cls._compute_dct_phash(im)
            return sha256, dhash, phash
        except Exception:
            return sha256, None, None

    def action_approve_and_publish(self):
        """Human approval action: publishes clean WebP derivatives to storefront gallery with strict provenance, deduplication & Odoo primary protection."""
        self._check_reviewer_rights()
        now = fields.Datetime.now()
        for review in self:
            if review.approval_status != "pending_review":
                raise UserError(_("Cannot approve asset '%s': current status is '%s'. Only pending assets can be approved.") % (review.name, review.approval_status))

            if review.source_type not in ELIGIBLE_APPROVAL_SOURCE_TYPES:
                raise UserError(_(
                    "Provenance Gate Blocked: Asset '%s' comes from source type '%s' (%s). "
                    "Only 'manufacturer' or explicitly licensed 'authorized_distributor' images are eligible for storefront approval."
                ) % (review.name, review.source_type, review.verified_domain or review.original_source_url))

            product = review.product_tmpl_id
            preview_data = review.webp_image or review.raw_image
            if not preview_data:
                raise UserError(_("No image binary available to publish for '%s'.") % review.name)

            cand_sha, cand_dhash, cand_phash = self._extract_image_fingerprint(preview_data)

            # Rule: External media NEVER occupies product.template.image_1920 (Slot 1).
            # Slot 1 is reserved exclusively for the original/internal Odoo product packshot.
            # External candidates can ONLY occupy Gallery Slots 2 & 3 (product.image).

            # Compare candidate against protected primary image (if present)
            if product.image_1920:
                prim_sha, prim_dhash, prim_phash = self._extract_image_fingerprint(product.image_1920)
                if cand_sha and prim_sha and cand_sha == prim_sha:
                    _logger.info("Review #%s rejected: exact duplicate of protected primary on product %s", review.id, product.id)
                    review.write({
                        "approval_status": "rejected",
                        "rejection_reason": "Decoded binary is an exact duplicate of the protected primary Odoo image.",
                    })
                    continue

                d_dist = bin(prim_dhash ^ cand_dhash).count('1') if (prim_dhash is not None and cand_dhash is not None) else 99
                p_dist = bin(prim_phash ^ cand_phash).count('1') if (prim_phash is not None and cand_phash is not None) else 99
                if d_dist <= 8 or p_dist <= 10:
                    _logger.info("Review #%s held in pending: perceptual near-duplicate (dDist=%d, pDist=%d) of primary on product %s", review.id, d_dist, p_dist, product.id)
                    review.write({
                        "rejection_reason": f"Perceptual near-duplicate of primary image (dHash dist={d_dist} <= 8, pHash dist={p_dist} <= 10); requires manual review.",
                    })
                    continue

            # Check candidate against all existing gallery images
            gallery_exact_dupe = False
            gallery_near_dupe = False
            for sib in product.product_template_image_ids:
                if not sib.image_1920:
                    continue
                sib_sha, sib_dhash, sib_phash = self._extract_image_fingerprint(sib.image_1920)
                if cand_sha and sib_sha and cand_sha == sib_sha:
                    gallery_exact_dupe = True
                    break
                s_ddist = bin(sib_dhash ^ cand_dhash).count('1') if (sib_dhash is not None and cand_dhash is not None) else 99
                s_pdist = bin(sib_phash ^ cand_phash).count('1') if (sib_phash is not None and cand_phash is not None) else 99
                if s_ddist <= 8 or s_pdist <= 10:
                    gallery_near_dupe = True
                    break

            if gallery_exact_dupe:
                _logger.info("Review #%s rejected: exact duplicate of existing gallery image on product %s", review.id, product.id)
                review.write({
                    "approval_status": "rejected",
                    "rejection_reason": "Decoded binary is an exact duplicate of an existing gallery image.",
                })
                continue

            if gallery_near_dupe:
                _logger.info("Review #%s held in pending: perceptual near-duplicate of existing gallery image on product %s", review.id, product.id)
                review.write({
                    "rejection_reason": "Perceptual near-duplicate of an existing gallery image; requires manual review.",
                })
                continue

            # Gallery Slot Capacity Gate: Slots 2 & 3 maximum
            if len(product.product_template_image_ids) >= 2:
                _logger.info("Review #%s held in pending: gallery slots full (2/2) on product %s", review.id, product.id)
                review.write({
                    "rejection_reason": "Gallery full (2/2 slots occupied); asset preserved in review archive.",
                })
                continue

            # Genuine, distinct external asset: publish strictly to gallery (Slot 2 or 3)
            self.env["product.image"].sudo().create({
                "name": review.name,
                "product_tmpl_id": product.id,
                "image_1920": preview_data,
            })
            review.write({
                "approval_status": "approved",
                "approved_by_id": self.env.uid,
                "approval_date": now,
                "rejection_reason": False,
            })

            product._recompute_image_quality_status()
            if hasattr(product, "_invalidate_product_shared_cache"):
                product._invalidate_product_shared_cache()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Image Approved & Published"),
                "message": _("Selected image(s) and responsive WebP derivatives published cleanly to product storefront."),
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
