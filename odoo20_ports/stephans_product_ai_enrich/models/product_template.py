# -*- coding: utf-8 -*-
import base64
import json
import logging
import re
import unicodedata
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

from odoo import api, fields, models, _
from odoo.exceptions import UserError, AccessError

_logger = logging.getLogger(__name__)

DEFAULT_SEEDED_URLS = """https://www.biolinepet.com/
https://summit10.com/dog/whole-choice/
https://unimarkpetfood.com/wp-content/themes/unimark/pdf/summit-en.pdf
https://tropicat.eu/
https://tropidog.eu/"""

DEFAULT_KEYWORDS = "premium pet care, safe natural ingredients, Dar es Salaam Tanzania, Stephan's Pet Store"

# ==============================================================================
# TECHNICAL RULE 1: STORE DATA PROTECTION
# Enrichment is strictly forbidden from modifying any store, price, cost, stock,
# warehouse, POS, tax, or publication availability field.
# ==============================================================================
PROTECTED_STORE_FIELDS = frozenset({
    'list_price', 'standard_price', 'lst_price', 'volume', 'weight',
    'qty_available', 'virtual_available', 'free_qty', 'incoming_qty', 'outgoing_qty',
    'route_ids', 'route_from_categ_ids', 'warehouse_id', 'location_id',
    'available_in_pos', 'pos_categ_ids', 'to_weight',
    'taxes_id', 'supplier_taxes_id',
    'active', 'is_published', 'website_published', 'sale_ok', 'purchase_ok',
    'company_id', 'website_id', 'categ_id', 'type', 'detailed_type', 'tracking',
})

# ==============================================================================
# INTERNATIONAL SOURCE PROVENANCE CLASSIFICATION
# Tier 1: Official Manufacturer Domains & Explicitly Licensed Distributors
# Tier 2: Trusted International Retailers (Cross-check only, never override manufacturer)
# ==============================================================================
MANUFACTURER_DOMAINS = (
    "summit10.com",
    "unimarkpetfood.com",
    "cotecnica.es",
    "ownat.com",
    "biolinepet.com",
    "tropicat.eu",
    "tropidog.eu",
    "tropical.pl",
    "tropifit.eu",
    "josera.com",
    "bravecto.com",
    "nexgard.com",
    "elanco.com",
    "f10products.co.uk",
    "whiskas.co.uk",
)

AUTHORIZED_DISTRIBUTOR_DOMAINS = (
    "stephanspetstore.co.tz",
)

TRUSTED_RETAILER_DOMAINS = (
    "ipet.ch",
    "zooroco.ch",
    "compapattes.fr",
    "vetforest.com",
    "petzone.com",
    "zooplus.com",
    "trixie.de",
    "ferplast.com",
)

FLAGSHIP_BRAND_KEYS = ('bioline', 'summit', 'tropicat', 'tropidog', 'tropifit', 'tropical')

OFFICIAL_BRAND_CATALOG_BRAIN = {
    # --- TIER 1: 4 ACTIVE FLAGSHIP BRANDS ---
    'bioline': {
        'label': 'Bioline',
        'tier': 1,
        'official_urls': [
            'https://www.biolinepet.com/',
        ],
        'trusted_retailer_urls': [
            'https://vetforest.com/',
            'https://www.petzone.com/',
        ],
        'search_templates': [
            'https://www.biolinepet.com/?s={query}',
        ],
        'keywords': 'Bioline pet care, gentle grooming, hygiene, safe formula, veterinary-grade, natural extracts',
        'synonyms': 'Bioline, Bioline Pet Care, grooming, hygiene',
        'guidelines': (
            'Official Bioline Pet Care product. Emphasize gentle, pet-safe formulation, '
            'hygiene/grooming benefits, clear directions for use, and accurate volume/weight.'
        ),
        'is_vet_medicine': False,
    },
    'summit': {
        'label': 'Summit 10',
        'tier': 1,
        'official_urls': [
            'https://summit10.com/dog/whole-choice/',
            'https://summit10.com/es/dog_es/whole-choice/cordero-fresco-para-perros-adultos/',
            'https://unimarkpetfood.com/wp-content/themes/unimark/pdf/summit-en.pdf',
            'https://summit10.com/',
        ],
        'trusted_retailer_urls': [
            'https://ipet.ch/en/our-pet-food-brands/summit10',
        ],
        'search_templates': [
            'https://summit10.com/?s={query}',
        ],
        'keywords': 'Summit 10, Summit10, super-premium nutrition, 10 natural ingredients, complete balanced pet food, Cotecnica Spain, Unimark Pet Food',
        'synonyms': 'Summit10, Summit 10, Summit-10, Cotecnica, Unimark, super premium, holistic pet nutrition',
        'guidelines': (
            'Official Summit 10 (Cotecnica, Spain / Unimark Pet Food catalogue) pet nutrition. Extract real meat/protein sources, '
            'analytical constituents (crude protein, fat, fiber, ash), life-stage/breed size, and daily feeding guide. '
            'Never allow retailer information to override official Summit10 or Unimark manufacturer specifications.'
        ),
        'is_vet_medicine': False,
    },
    'tropicat': {
        'label': 'TropiCat',
        'tier': 1,
        'official_urls': [
            'https://tropicat.eu/',
            'https://tropical.pl/en/',
        ],
        'trusted_retailer_urls': [],
        'search_templates': [
            'https://tropicat.eu/?s={query}',
        ],
        'keywords': 'TropiCat, Tropical Poland, complete cat nutrition, taurine, healthy digestion, coat shine',
        'synonyms': 'TropiCat, Tropi Cat, Tropi-Cat, Tropical Poland, feline nutrition',
        'guidelines': (
            'Official TropiCat (Tropical, Poland) cat food. Emphasize balanced feline nutrition, '
            'taurine support, hairball/urinary/coat care, exact ingredients, and feeding recommendations.'
        ),
        'is_vet_medicine': False,
    },
    'tropidog': {
        'label': 'TropiDog',
        'tier': 1,
        'official_urls': [
            'https://tropidog.eu/',
            'https://tropical.pl/en/',
        ],
        'trusted_retailer_urls': [],
        'search_templates': [
            'https://tropidog.eu/?s={query}',
        ],
        'keywords': 'TropiDog, Tropical Poland, premium dog nutrition, omega fatty acids, dental & joint care',
        'synonyms': 'TropiDog, Tropi Dog, Tropi-Dog, Tropical Poland, canine nutrition',
        'guidelines': (
            'Official TropiDog (Tropical, Poland) dog food. Highlight real protein sources, '
            'breed size suitability, digestive/joint/coat benefits, analytical constituents, and feeding guide.'
        ),
        'is_vet_medicine': False,
    },
    'tropifit': {
        'label': 'Tropifit',
        'tier': 1,
        'official_urls': [
            'https://tropifit.eu/',
            'https://tropical.pl/en/',
        ],
        'trusted_retailer_urls': [],
        'search_templates': [
            'https://tropifit.eu/?s={query}',
        ],
        'keywords': 'Tropifit, Tropical Poland, small animal nutrition, rabbit, guinea pig, hamster, natural herbs & fiber',
        'synonyms': 'Tropifit, Tropi Fit, Tropical Poland, small animal food, rodent food',
        'guidelines': (
            'Official Tropifit (Tropical, Poland) small-animal food. Highlight species suitability, '
            'natural fiber/herbs, dental wear support, vitamins, and daily feeding guide.'
        ),
        'is_vet_medicine': False,
    },
    'tropical': {
        'label': 'Tropical',
        'tier': 1,
        'official_urls': [
            'https://tropical.pl/en/',
        ],
        'trusted_retailer_urls': [],
        'search_templates': [
            'https://tropical.pl/en/?s={query}',
        ],
        'keywords': 'Tropical Poland, aquarium fish food, flakes, granules, balanced aquatic nutrition',
        'synonyms': 'Tropical, Tropical Poland, fish food, aquatic nutrition',
        'guidelines': (
            'Official Tropical (Poland) aquatic & pet care. Highlight fish species suitability, '
            'water clarity (non-clouding), vitamins, and feeding instructions.'
        ),
        'is_vet_medicine': False,
    },
    # --- TIER 2: SECONDARY BRANDS & VETERINARY ---
    'bravecto': {
        'label': 'Bravecto',
        'tier': 2,
        'official_urls': ['https://www.bravecto.com/'],
        'trusted_retailer_urls': [],
        'search_templates': [],
        'keywords': 'Bravecto, MSD Animal Health, fluralaner, 12-week flea and tick protection',
        'synonyms': 'Bravecto, MSD Animal Health, fluralaner, flea tick chewable spot-on',
        'guidelines': 'Official MSD Animal Health Bravecto. Strictly preserve the exact pet weight band in the product name. Never invent dosages.',
        'is_vet_medicine': True,
    },
    'nexgard': {
        'label': 'NexGard',
        'tier': 2,
        'official_urls': ['https://www.nexgard.com/'],
        'trusted_retailer_urls': [],
        'search_templates': [],
        'keywords': 'NexGard Spectra, Boehringer Ingelheim, flea tick worm chewable',
        'synonyms': 'NexGard, NexGard Spectra, Nex Gard, Boehringer Ingelheim, parasite protection',
        'guidelines': 'Official Boehringer Ingelheim NexGard. Strictly preserve the exact weight range in the title. Never invent dosages.',
        'is_vet_medicine': True,
    },
    'milbemax': {
        'label': 'Milbemax',
        'tier': 2,
        'official_urls': ['https://www.elanco.com/'],
        'trusted_retailer_urls': [],
        'search_templates': [],
        'keywords': 'Milbemax, Elanco, broad-spectrum dewormer tablets',
        'synonyms': 'Milbemax, Elanco, dewormer, worming tablet',
        'guidelines': 'Official Elanco Milbemax dewormer. Strictly preserve pet species and weight band. Never invent dosages.',
        'is_vet_medicine': True,
    },
    'f10': {
        'label': 'F10',
        'tier': 2,
        'official_urls': ['https://www.f10products.co.uk/'],
        'trusted_retailer_urls': [],
        'search_templates': [],
        'keywords': 'F10 Veterinary Products, germicidal, antiseptic wound care',
        'synonyms': 'F10, F10SC, F10 Germicidal, veterinary disinfectant ointment',
        'guidelines': 'Official F10 Veterinary Products. Include safe veterinary usage directions.',
        'is_vet_medicine': True,
    },
    'josera': {
        'label': 'Josera',
        'tier': 2,
        'official_urls': ['https://www.josera.com/'],
        'trusted_retailer_urls': [],
        'search_templates': ['https://www.josera.com/catalogsearch/result/?q={query}'],
        'keywords': 'Josera Germany, super-premium pet food, no artificial colors or preservatives',
        'synonyms': 'Josera, Josera Germany, German pet food',
        'guidelines': 'Official Josera (Germany) pet food. Highlight German quality, ingredients, and feeding guidelines.',
        'is_vet_medicine': False,
    },
    'whiskas': {
        'label': 'Whiskas',
        'tier': 2,
        'official_urls': ['https://www.whiskas.co.uk/'],
        'trusted_retailer_urls': [],
        'search_templates': [],
        'keywords': 'Whiskas, Mars Petcare, complete cat food, balanced nutrition',
        'synonyms': 'Whiskas, cat pouch, feline food',
        'guidelines': 'Official Whiskas cat food. Highlight flavor, life-stage nutrition, and feeding guide.',
        'is_vet_medicine': False,
    },
    'ownat': {
        'label': 'Ownat',
        'tier': 2,
        'official_urls': ['https://www.ownat.com/en/'],
        'trusted_retailer_urls': [],
        'search_templates': [],
        'keywords': 'Ownat, Cotecnica Spain, natural ingredients, fresh meat pet food',
        'synonyms': 'Ownat, Cotecnica, natural pet food',
        'guidelines': 'Official Ownat (Cotecnica, Spain) natural pet food. Highlight natural ingredients and feeding guide.',
        'is_vet_medicine': False,
    },
}

GENERAL_CATALOG_FALLBACK_URLS = [
    'https://ipet.ch/en/our-pet-food-brands/summit10',
    'https://www.petzone.com/',
    'https://www.zooplus.com/',
    'https://www.trixie.de/en/',
    'https://www.ferplast.com/',
]

SEARCH_REBUILD_TRIGGER_FIELDS = frozenset({
    'name', 'default_code', 'barcode',
    'x_keywords', 'x_search_synonyms', 'x_structured_queries',
    'x_key_ingredients', 'x_packaging_form',
    'public_categ_ids', 'categ_id',
    'product_brand_id', 'brand_id',
})

CACHE_INVALIDATION_TRIGGER_FIELDS = SEARCH_REBUILD_TRIGGER_FIELDS | frozenset({
    'list_price', 'is_published', 'website_published', 'active',
    'image_1920', 'image_1024', 'image_512', 'image_256', 'image_128',
    'website_description', 'description_sale',
})


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _auto_init(self):
        """Install the search acceleration schema reproducibly on every database."""
        result = super()._auto_init()
        try:
            with self.env.cr.savepoint():
                self.env.cr.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
                self.env.cr.execute(
                    """
                    CREATE INDEX IF NOT EXISTS product_template_x_search_index_trgm_idx
                    ON product_template USING gin (x_search_index gin_trgm_ops)
                    WHERE x_search_index IS NOT NULL
                    """
                )
        except Exception:
            _logger.exception(
                "Could not create the pg_trgm search index; catalogue search will continue without it"
            )
        return result

    x_source_urls = fields.Text(
        string="Reference URLs (Catalog Seeds)",
        default=DEFAULT_SEEDED_URLS,
        help="Official manufacturer or trusted pet catalogue links (one per line) used by the AI engine."
    )
    x_keywords = fields.Char(
        string="Target Keywords & Highlights",
        default=DEFAULT_KEYWORDS,
        help="Comma-separated keywords or selling points to emphasize in AI generated descriptions."
    )
    x_search_synonyms = fields.Char(
        string="Search Synonyms & Pack Aliases",
        help="Normalized synonyms, species aliases, manufacturer codes, and pack size variations (e.g. Summit10, Summit 10, Summit-10, lamb, fresh lamb, 2kg, 2 kg, 2000g, C1202)."
    )
    x_structured_queries = fields.Text(
        string="Structured Enrichment Queries",
        help="Exact structured manufacturer search queries used for verification against Summit10, Unimark, and trusted catalogues."
    )
    x_search_index = fields.Text(
        string="Normalized Search Index",
        compute="_compute_x_search_index",
        store=True,
        index=True,
        help="Precomputed normalized search string (product name + SKU + brand + category + synonyms + pack size) for fast single-field indexed lookup."
    )
    x_key_ingredients = fields.Text(
        string="Key Ingredients / Composition",
        help="Extracted raw materials or ingredients."
    )
    x_packaging_form = fields.Char(
        string="Packaging & Form",
        help="Physical form and packaging."
    )
    # Staged suggestion fields (Nothing publishes automatically)
    x_suggested_name = fields.Char(
        string="Suggested Product Name (Staged)",
        readonly=True,
        help="AI-prepared product title pending human review before publishing."
    )
    x_suggested_description = fields.Html(
        string="Suggested Website Description (Staged)",
        readonly=True,
        sanitize=False,
        help="AI-prepared storefront HTML description pending human review before publishing."
    )
    x_suggested_description_sale = fields.Text(
        string="Suggested Sales Description (Staged)",
        readonly=True,
        help="AI-prepared plain description pending human review before publishing."
    )
    x_enrichment_status = fields.Selection(
        [
            ("draft", "Unenriched"),
            ("pending_review", "Staged for Human Review"),
            ("approved", "Approved & Published"),
            ("rejected", "Rejected"),
        ],
        string="Enrichment Approval Status",
        default="draft",
        index=True,
    )
    x_is_vet_medicine = fields.Boolean(
        string="Veterinary Medicine (Manual Approval Mandatory)",
        default=False,
        help="Veterinary medicines require strict manual verification of all dosage, weight-band, and medical claims before approval."
    )
    x_ai_enriched = fields.Boolean(
        string="AI Enriched",
        default=False,
        index=True,
        help="Checked once this product has been processed by the AI Catalog Engine."
    )
    x_ai_last_enriched = fields.Datetime(
        string="Last AI Enrichment",
        readonly=True,
    )
    x_ai_last_error = fields.Text(
        string="Last AI Error",
        readonly=True,
    )
    image_review_ids = fields.One2many(
        "product.image.review",
        "product_tmpl_id",
        string="Media Review Queue",
    )
    image_review_count = fields.Integer(
        string="Review Images Count",
        compute="_compute_image_review_count",
    )
    image_quality_status = fields.Selection(
        [
            ("uninspected", "Uninspected"),
            ("pending_review", "Images in Review Queue"),
            ("approved", "Images Approved & Published"),
            ("rejected", "Images Rejected"),
        ],
        string="Media Quality Gate",
        default="uninspected",
        index=True,
    )

    @staticmethod
    def _assert_store_data_protected(vals):
        """Technical Rule #1: Strictly prevent enrichment from touching store, price, inventory, POS, or tax data."""
        forbidden = PROTECTED_STORE_FIELDS.intersection(vals.keys())
        if forbidden:
            raise UserError(_(
                "Store Data Protection Violation: Enrichment attempted to modify protected store fields: %s. "
                "Prices, cost, inventory, POS configuration, taxes, and availability are strictly read-only."
            ) % ", ".join(sorted(forbidden)))

    @staticmethod
    def _normalize_text_for_index(text):
        if not text:
            return ""
        decomposed = unicodedata.normalize("NFD", str(text))
        stripped = "".join(c for c in decomposed if unicodedata.category(c) != "Mn")
        return stripped.lower()

    @api.depends(
        "name",
        "default_code",
        "barcode",
        "x_keywords",
        "x_search_synonyms",
        "x_key_ingredients",
        "x_packaging_form",
        "public_categ_ids.name",
        "categ_id.name",
    )
    def _compute_x_search_index(self):
        """
        Build a lightweight stored normalized search index per product:
        product name + SKU + brand + category + synonyms + pack size
        Example:
        summit 10 summit10 whole choice adult dog fresh lamb lamb dry food grain free medium large breed 2kg 2 kg 2000g s-item0843 sitem0843 c1202
        """
        for rec in self:
            parts = []
            raw_name = self._normalize_text_for_index(rec.name or "")
            if raw_name:
                parts.append(raw_name)
                # Compact alphanumeric variation (e.g. "summit 10" -> "summit10", "s-item0843" -> "sitem0843")
                parts.append(re.sub(r"[\s\-_]+", "", raw_name))
                # Space-separated variation for hyphenated words
                parts.append(re.sub(r"[\-_/.,]+", " ", raw_name))

            sku = self._normalize_text_for_index(rec.default_code or "")
            if sku:
                parts.append(sku)
                parts.append(re.sub(r"[\s\-_]+", "", sku))

            barcode = self._normalize_text_for_index(rec.barcode or "")
            if barcode:
                parts.append(barcode)

            # Brand & Brand Synonyms
            brand_key, profile = rec._detect_brand_profile()
            if profile:
                parts.append(self._normalize_text_for_index(profile.get("label", "")))
                parts.append(self._normalize_text_for_index(profile.get("synonyms", "")))
            if hasattr(rec, "product_brand_id") and rec.product_brand_id and rec.product_brand_id.name:
                bname = self._normalize_text_for_index(rec.product_brand_id.name)
                parts.append(bname)
                parts.append(re.sub(r"[\s\-_]+", "", bname))
            if hasattr(rec, "brand_id") and rec.brand_id and rec.brand_id.name:
                bname = self._normalize_text_for_index(rec.brand_id.name)
                parts.append(bname)
                parts.append(re.sub(r"[\s\-_]+", "", bname))

            # Categories
            if hasattr(rec, "public_categ_ids") and rec.public_categ_ids:
                for pc in rec.public_categ_ids:
                    if pc.name:
                        parts.append(self._normalize_text_for_index(pc.name))
            if rec.categ_id and rec.categ_id.name:
                parts.append(self._normalize_text_for_index(rec.categ_id.name))

            # Pack size expansions (e.g. 2kg <-> 2 kg <-> 2000g, 3kg <-> 3 kg <-> 3000g, 10kg <-> 10 kg <-> 10000g)
            for match in re.finditer(r"\b(\d+(?:\.\d+)?)\s*(kg|g|l|ml|pcs|capsules)\b", raw_name):
                val_str, unit = match.group(1), match.group(2)
                parts.append(f"{val_str}{unit}")
                parts.append(f"{val_str} {unit}")
                try:
                    val_num = float(val_str)
                    if unit == "kg":
                        grams = int(val_num * 1000)
                        parts.append(f"{grams}g {grams} g")
                    elif unit == "l":
                        mls = int(val_num * 1000)
                        parts.append(f"{mls}ml {mls} ml {val_str} liter {val_str} litre")
                except Exception:
                    pass

            # Species & life-stage synonyms
            if "dog" in raw_name or "puppy" in raw_name:
                parts.append("dog dogs canine")
            if "puppy" in raw_name:
                parts.append("puppy puppies junior young dog")
            if "cat" in raw_name or "kitten" in raw_name:
                parts.append("cat cats feline")
            if "kitten" in raw_name:
                parts.append("kitten kittens junior young cat")
            if "grain free" in raw_name or "grain-free" in raw_name:
                parts.append("grain free grainfree")

            # Custom synonyms, keywords, ingredients, packaging
            for extra_field in (rec.x_search_synonyms, rec.x_keywords, rec.x_key_ingredients, rec.x_packaging_form):
                if extra_field:
                    norm_extra = self._normalize_text_for_index(extra_field)
                    parts.append(norm_extra)
                    parts.append(re.sub(r"[,;|/]+", " ", norm_extra))

            # Deduplicate tokens while preserving order
            tokens = []
            seen = set()
            for token in " ".join(parts).split():
                clean_tok = token.strip(",.;:()[]{}\"'")
                if clean_tok and clean_tok not in seen:
                    seen.add(clean_tok)
                    tokens.append(clean_tok)

            rec.x_search_index = " ".join(tokens)

    def _invalidate_product_shared_cache(self):
        """Invalidate only this product's cached search/brand/homepage entries in the shared cache."""
        if not self.ids:
            return
        try:
            from odoo.addons.stephans_website_theme.models.shared_cache import invalidate_product_cache
            invalidate_product_cache(self.ids, env=self.env)
        except Exception as e:
            _logger.debug("Shared cache invalidation skipped: %s", e)

    def write(self, vals):
        res = super().write(vals)
        if CACHE_INVALIDATION_TRIGGER_FIELDS.intersection(vals.keys()):
            self._invalidate_product_shared_cache()
        return res

    @api.model
    def _search_get_detail(self, website, order, options):
        """
        Optimize Odoo 20 standard `/shop?search=...` by routing search queries to the indexed
        `x_search_index` column instead of scanning unindexed `website_description` HTML blobs.
        """
        res = super()._search_get_detail(website, order, options)
        if "x_search_index" in self._fields:
            res["search_fields"] = ["x_search_index", "name", "default_code"]
            res["fetch_fields"] = [f for f in res.get("fetch_fields", []) if f != "website_description"]
            mapping = res.get("mapping", {})
            mapping.pop("description", None)
            if "detail_description" in mapping:
                mapping["detail_description"] = {"name": "description_sale", "type": "text", "match": True}
        return res

    @api.depends("image_review_ids")
    def _compute_image_review_count(self):
        for product in self:
            product.image_review_count = len(product.image_review_ids)

    def action_view_image_review_queue(self):
        self.ensure_one()
        return {
            "name": f"Media Review Queue - {self.display_name}",
            "type": "ir.actions.act_window",
            "res_model": "product.image.review",
            "domain": [("product_tmpl_id", "=", self.id)],
            "view_mode": "list,kanban,form",
            "context": {"default_product_tmpl_id": self.id},
        }

    def _detect_brand_profile(self):
        """Match this product against the Official Brand Catalog Brain."""
        self.ensure_one()
        haystack = (self.name or '').lower()
        if hasattr(self, 'product_brand_id') and self.product_brand_id and self.product_brand_id.name:
            haystack += ' ' + self.product_brand_id.name.lower()
        if hasattr(self, 'brand_id') and self.brand_id and self.brand_id.name:
            haystack += ' ' + self.brand_id.name.lower()

        for key, profile in OFFICIAL_BRAND_CATALOG_BRAIN.items():
            if key in haystack:
                return key, profile
        return None, None

    @staticmethod
    def _classify_domain_provenance(hostname):
        """
        Classify domain strictly into one of the 4 standardized provenance tiers:
        - manufacturer
        - authorized_distributor
        - trusted_retailer
        - external_unverified
        """
        if not hostname:
            return "external_unverified", "Unknown hostname"
        h = hostname.lower()
        if any(h == d or h.endswith("." + d) for d in MANUFACTURER_DOMAINS):
            return "manufacturer", f"Verified Tier-1 official manufacturer asset from {h}"
        if any(h == d or h.endswith("." + d) for d in AUTHORIZED_DISTRIBUTOR_DOMAINS):
            return "authorized_distributor", f"Verified authorized distributor asset from {h}"
        if any(h == d or h.endswith("." + d) for d in TRUSTED_RETAILER_DOMAINS):
            return "trusted_retailer", f"Tier-2 trusted international retailer ({h}) - cross-check only; not eligible for direct image publishing without license confirmation"
        return "external_unverified", f"External unverified asset from {h} - requires provenance verification"

    def _build_structured_enrichment_queries(self):
        """Build structured manufacturer & specification queries for this product."""
        self.ensure_one()
        _, profile = self._detect_brand_profile()
        brand_label = profile["label"] if profile else "Stephan's Pet Store"
        brand_compact = re.sub(r"\s+", "", brand_label)
        raw_name = (self.name or "").strip()

        # Extract pack size
        size_match = re.search(r"\b(\d+(?:\.\d+)?\s*(?:kg|g|l|ml|pcs|capsules))\b", raw_name, flags=re.IGNORECASE)
        pack_size = size_match.group(1) if size_match else ""

        # Core title without brand and pack size
        core_title = re.sub(re.escape(brand_label), "", raw_name, flags=re.IGNORECASE)
        if pack_size:
            core_title = re.sub(re.escape(pack_size), "", core_title, flags=re.IGNORECASE)
        core_title = re.sub(r"\s+", " ", core_title).strip(" -–,")

        sku = (self.default_code or "").strip()
        queries = [
            f'"{brand_label}" "{core_title}" "{pack_size}"'.replace(' ""', '').strip(),
            f'"{brand_compact}" "{sku}"'.replace(' ""', '').strip(),
        ]
        if profile and "summit" in (brand_label or "").lower():
            queries.extend([
                f'site:summit10.com "{core_title}"',
                f'site:unimarkpetfood.com "{core_title}"',
                f'"{brand_label} {core_title}" ingredients',
                f'"{brand_label} {core_title}" analytical constituents',
                f'"{brand_label} {core_title}" feeding guide',
            ])
        elif profile and profile.get("official_urls"):
            parsed_host = urllib.parse.urlparse(profile["official_urls"][0]).hostname or ""
            if parsed_host:
                queries.append(f'site:{parsed_host} "{core_title}"')
                queries.append(f'"{brand_label} {core_title}" ingredients')
        return "\n".join(q for q in queries if q)

    def _build_official_seed_urls(self):
        """Build official brand Tier-1 manufacturer URLs + Tier-2 cross-check URLs."""
        self.ensure_one()
        _, profile = self._detect_brand_profile()
        clean_name = re.sub(r'\s+', ' ', (self.name or '').strip())
        short_query = ' '.join(clean_name.split()[:5])
        encoded_q = urllib.parse.quote_plus(short_query)

        urls = []
        if profile:
            for u in profile.get('official_urls', []):
                if u not in urls:
                    urls.append(u)
            for tmpl in profile.get('search_templates', []):
                u = tmpl.format(query=encoded_q)
                if u not in urls:
                    urls.append(u)
            for r_url in profile.get('trusted_retailer_urls', []):
                if r_url not in urls:
                    urls.append(r_url)
        else:
            urls.extend(GENERAL_CATALOG_FALLBACK_URLS)
        return urls

    def action_seed_official_brand_urls(self):
        """Seed official manufacturer URLs, structured queries & synonyms without modifying protected store fields."""
        for rec in self:
            _, profile = rec._detect_brand_profile()
            official_urls = rec._build_official_seed_urls()

            existing = [
                u.strip() for u in (rec.x_source_urls or '').splitlines()
                if u.strip().startswith('http')
                and 'amazon.ae/Bioline-Tofu' not in u
                and 'katzeom.com/products/bioline-tofu' not in u
                and 'noon.com/uae-en/bioline-tofu' not in u
                and 'preview.stephanspetstore.co.tz' not in u
                and 'summit10.com/en/product/' not in u
            ]
            merged = []
            for u in official_urls + existing:
                if u not in merged:
                    merged.append(u)

            vals = {
                'x_source_urls': '\n'.join(merged[:8]),
                'x_structured_queries': rec._build_structured_enrichment_queries(),
            }
            if profile:
                vals['x_is_vet_medicine'] = bool(profile.get('is_vet_medicine', False))
                if not rec.x_keywords or rec.x_keywords == DEFAULT_KEYWORDS or 'okara bean dregs' in (rec.x_keywords or '').lower():
                    if 'litter' not in (rec.name or '').lower():
                        vals['x_keywords'] = profile['keywords']
                if not rec.x_search_synonyms:
                    vals['x_search_synonyms'] = profile.get('synonyms', '')

            self._assert_store_data_protected(vals)
            rec.write(vals)
        return True

    def _validate_enrichment_gates(self, ai_data):
        """
        Error-Prevention Gates before any description enters Odoo staging:
        1. Match brand.
        2. Match exact pack size.
        3. Match species and life stage.
        4. Reject conflicting dosage/weight-band alterations on veterinary medicines.
        """
        self.ensure_one()
        orig_name = (self.name or "").strip()
        orig_lower = orig_name.lower()
        suggested_title = self._strip_emojis(ai_data.get("title") or orig_name)
        sugg_lower = suggested_title.lower()

        # Gate 1: Match Brand
        _, profile = self._detect_brand_profile()
        if profile:
            brand_label = profile["label"].lower()
            brand_first = brand_label.split()[0]
            if brand_first not in sugg_lower:
                raise UserError(_(
                    "Error-Prevention Gate (Brand Mismatch): Current product belongs to brand '%s', "
                    "but AI suggested title '%s' omits the brand."
                ) % (profile["label"], suggested_title))

        # Gate 2: Match Exact Pack Size (e.g. 2kg vs 10kg, 3kg, 85g, 6L, 60 Capsules)
        orig_sizes = [m.group(0).lower().replace(" ", "") for m in re.finditer(r"\b\d+(?:\.\d+)?\s*(?:kg|g|l|ml|pcs|capsules)\b", orig_lower)]
        if orig_sizes:
            sugg_normalized = re.sub(r"\s+", "", sugg_lower)
            for req_size in orig_sizes:
                if req_size not in sugg_normalized:
                    raise UserError(_(
                        "Error-Prevention Gate (Pack Size Mismatch): Current product specifies pack size '%s' (%s), "
                        "but suggested title '%s' does not match the exact pack size."
                    ) % (req_size, orig_name, suggested_title))

        # Gate 3: Match Species & Life Stage
        species_Pairs = [
            ("dog", ("cat", "kitten", "feline")),
            ("puppy", ("cat", "kitten", "feline", "senior")),
            ("cat", ("dog", "puppy", "canine")),
            ("kitten", ("dog", "puppy", "canine", "senior")),
        ]
        for token, forbidden_conflicts in species_Pairs:
            if re.search(rf"\b{token}\b", orig_lower) and not re.search(rf"\b({ '|'.join(forbidden_conflicts) })\b", orig_lower):
                if not re.search(rf"\b{token}\b", sugg_lower):
                    # Ensure suggested title didn't flip species
                    for conflict in forbidden_conflicts:
                        if re.search(rf"\b{conflict}\b", sugg_lower):
                            raise UserError(_(
                                "Error-Prevention Gate (Species/Life-Stage Conflict): Product '%s' is for '%s', "
                                "but suggested output mentions conflicting species/stage '%s'."
                            ) % (orig_name, token, conflict))

        return True

    def action_regenerate_ai_details(self):
        """
        Prepare and stage AI suggestions & candidate images into the Human Review Queue.
        Nothing publishes automatically, and protected store fields are strictly untouched.
        """
        self.ensure_one()

        if not self.x_source_urls or 'amazon.ae/Bioline-Tofu' in (self.x_source_urls or '') or 'summit10.com/en/product/' in (self.x_source_urls or ''):
            if 'litter' not in (self.name or '').lower():
                self.action_seed_official_brand_urls()

        # 1. Fetch & parse content from Tier-1 manufacturer & Tier-2 cross-check URLs
        scraped_text, image_candidates = self._fetch_catalog_sources()

        # 2. Query AI Engine
        ai_data = self._call_ai_engine(scraped_text, image_candidates)

        # 3. Validate Error-Prevention Gates (Brand, Pack Size, Species, Life Stage)
        self._validate_enrichment_gates(ai_data)

        # 4. Stage outputs into review fields (Never auto-publish!)
        self._stage_ai_data_for_review(ai_data)

        status_vals = {
            'x_ai_enriched': True,
            'x_ai_last_enriched': fields.Datetime.now(),
            'x_ai_last_error': False,
        }
        self._assert_store_data_protected(status_vals)
        self.write(status_vals)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('AI Enrichment Staged for Review'),
                'message': _(
                    "Product '%s' suggestions and candidate images have been validated and staged in the Review Queue. "
                    "Review and click 'Approve Enrichment' to publish."
                ) % self.name,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_approve_ai_enrichment(self):
        """
        Human Review Approval Action:
        Applies the staged description and metadata suggestions to the product record
        while keeping all store prices, stock, POS, and warehouse fields strictly protected.
        """
        if not self.env.user.has_group("stephans_product_ai_enrich.group_media_reviewer") and not self.env.is_admin():
            raise AccessError(_("Permission Denied: Only authorized Catalog Reviewers can approve product enrichment."))

        for rec in self:
            if rec.x_enrichment_status != "pending_review" and not rec.x_suggested_description:
                raise UserError(_("Product '%s' has no staged AI enrichment pending approval.") % rec.name)

            vals = {
                'x_enrichment_status': 'approved',
            }
            if rec.x_suggested_description:
                vals['website_description'] = rec.x_suggested_description
            if rec.x_suggested_description_sale:
                vals['description_sale'] = rec.x_suggested_description_sale

            # Strictly verify no protected store fields are touched
            self._assert_store_data_protected(vals)
            rec.write(vals)
            rec._invalidate_product_shared_cache()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Enrichment Approved & Published'),
                'message': _('Approved description suggestions have been published and search cache updated.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_reject_ai_enrichment(self):
        """Reject staged AI text suggestions without altering live product descriptions."""
        for rec in self:
            vals = {
                'x_enrichment_status': 'rejected',
            }
            self._assert_store_data_protected(vals)
            rec.write(vals)
        return True

    @api.model
    def cron_auto_enrich_products(self, limit=5):
        """
        Controlled Batch Enrich (Default limit=5 products per batch).
        Prepares and stages up to 5 products into the review queue. Never auto-publishes.
        """
        limit = min(int(limit or 5), 5)
        ir_config = self.env['ir.config_parameter'].sudo()
        gemini_key = (ir_config.get_param('stephans_product_ai_enrich.gemini_api_key') or '').strip()
        openai_key = (ir_config.get_param('stephans_product_ai_enrich.openai_api_key') or '').strip()
        if not gemini_key and not openai_key:
            _logger.info("AI Batch Enrich skipped: No Gemini or OpenAI API key configured.")
            return

        base_domain = [
            ('active', '=', True),
            ('sale_ok', '=', True),
            ('x_ai_enriched', '=', False),
            ('x_ai_last_error', '=', False),
        ]

        flagship_or = ['|'] * (len(FLAGSHIP_BRAND_KEYS) - 1)
        for bk in FLAGSHIP_BRAND_KEYS:
            flagship_or.append(('name', 'ilike', bk))

        batch = self.search(
            base_domain + flagship_or,
            order='is_published desc, list_price desc, id asc',
            limit=limit,
        )

        if len(batch) < limit:
            remaining = limit - len(batch)
            extra = self.search(
                base_domain + [('id', 'not in', batch.ids)],
                order='is_published desc, list_price desc, id asc',
                limit=remaining,
            )
            batch |= extra

        if not batch:
            _logger.info("AI Batch Enrich: No unenriched products remaining.")
            return

        _logger.info("AI Batch Enrich: Staging batch of %d products for review: %s", len(batch), batch.mapped('name'))
        for product in batch:
            try:
                product.action_seed_official_brand_urls()
                product.action_regenerate_ai_details()
                self.env.cr.commit()
                _logger.info("AI Batch Enrich: Staged [%s] %s for human review", product.id, product.name)
            except Exception as e:
                self.env.cr.rollback()
                err_msg = str(e)[:500]
                _logger.warning("AI Batch Enrich: Failed on [%s] %s: %s", product.id, product.name, err_msg)
                if not any(code in err_msg for code in ('401', '403', '429', 'configure your')):
                    product.write({'x_ai_last_error': err_msg})
                    self.env.cr.commit()
                else:
                    break

    def _fetch_catalog_sources(self):
        """Fetch raw HTML, text and high-res clean images from seeded URLs, tagging each by source tier."""
        urls = [u.strip() for u in (self.x_source_urls or '').split('\n') if u.strip().startswith('http')]
        combined_text = (
            f"Current Product Name: {self.name}\n"
            f"Default SKU: {self.default_code or ''}\n"
            f"Structured Queries:\n{self.x_structured_queries or ''}\n"
            f"User Target Keywords: {self.x_keywords or ''}\n"
            f"Search Synonyms: {self.x_search_synonyms or ''}\n\n"
        )
        image_candidates = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        for url in urls:
            try:
                parsed = urllib.parse.urlparse(url)
                source_tier, _ = self._classify_domain_provenance(parsed.hostname)
                if url.lower().endswith('.pdf'):
                    combined_text += f"\n--- Source Reference ({source_tier.upper()} PDF Catalogue): {url} ---\n"
                    continue

                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(html, 'html.parser')

                    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'svg']):
                        tag.decompose()

                    text = soup.get_text(' ', strip=True)[:3500]
                    combined_text += f"\n--- Source URL ({source_tier.upper()}): {url} ---\n{text}\n"

                    # Collect candidate images ONLY from manufacturer or authorized_distributor sources
                    if source_tier in ('manufacturer', 'authorized_distributor'):
                        for img in soup.find_all('img'):
                            src = img.get('src') or img.get('data-src') or ''
                            if not src:
                                continue
                            if src.startswith('//'):
                                src = 'https:' + src
                            elif src.startswith('/'):
                                src = f"{parsed.scheme}://{parsed.netloc}{src}"

                            src_lower = src.lower()
                            if any(b in src_lower for b in ['logo', 'icon', 'badge', 'payment', 'watermark', 'banner', 'thumb', 'avatar', 'flag']):
                                continue

                            full_res_src = re.sub(r'_\d+x\d*\.', '.', src)
                            full_res_src = re.sub(r'width=\d+', 'width=1920', full_res_src)

                            if full_res_src not in image_candidates and full_res_src.startswith('http'):
                                image_candidates.append(full_res_src)

            except Exception as e:
                _logger.warning("Error fetching catalog source %s: %s", url, e)

        return combined_text, image_candidates[:10]

    def _build_catalog_prompt(self, context_text, image_candidates):
        """Construct the prompt enforcing the Stephan's Pet Store catalog formula & safety rules"""
        _, profile = self._detect_brand_profile()
        brand_block = ""
        vet_safety_block = ""
        if profile:
            brand_block = (
                f"\nOFFICIAL BRAND BRAIN ({profile['label']}):\n"
                f"- Tier-1 Official Manufacturer Websites: {', '.join(profile.get('official_urls', []))}\n"
                f"- Tier-2 Retailer Cross-Check URLs: {', '.join(profile.get('trusted_retailer_urls', []))}\n"
                f"- Brand Guidelines: {profile.get('guidelines', '')}\n"
                f"- Provenance Rule: Retailer information must NEVER override official manufacturer specifications.\n"
            )
            if profile.get('is_vet_medicine'):
                vet_safety_block = (
                    "\nMANDATORY VETERINARY SAFETY RULE:\n"
                    "- This is a veterinary/parasite-control product. Strictly preserve the exact pet weight band and species.\n"
                    "- NEVER invent medical dosages or off-label claims.\n"
                    "- Include 'Always consult your veterinarian before administration and follow package weight guidelines.' in instructions_steps.\n"
                )

        return f"""
You are the master e-commerce catalog director for Stephan's Pet Store (Tanzania).
Your task is to analyze the official manufacturer catalogue texts, structured queries, and candidate image URLs below,
and output standardized, factual, healthy, high-converting product data in valid JSON.
{brand_block}{vet_safety_block}
STRICT ACCURACY & ERROR-PREVENTION GATES:
- Match exact brand, exact pack size (e.g. 2kg vs 10kg), SKU, species, and life stage of "{self.name}".
- Ground all ingredients, analytical constituents (protein/fat/fiber/ash percentages), sizes, and feeding guides strictly in official manufacturer facts.
- Do NOT hallucinate fake ingredients, fake barcodes, or unverified medical claims.

Reference Content:
{context_text}

Available Manufacturer Image URLs:
{json.dumps(image_candidates, indent=2)}

CRITICAL FORMULA REQUIREMENTS:
All products in Stephan's Pet Store MUST follow the exact same visual hierarchy and clean professional styling:
- STRICT NO-EMOJI RULE: Never output emojis, unicode icons, or cartoon symbols in any title, header, bullet, or description. Use clean, elegant typography.
1. title: Clean, standardized format preserving the exact pack size: [Brand] [Product Line / Feature] [Size or Weight]
2. barcode: Manufacturer EAN-13 or UPC barcode if verified (or empty string).
3. lead_summary: 1-2 compelling executive summary sentences explaining the core formula, technology, and primary benefit.
4. key_highlights: Array of 4 to 6 highlights, each with a clean bold header and detailed explanation (NO emojis/icons).
5. composition_title: 'Composition & Ingredients' (or 'Materials & Specifications' for accessories) - NO emojis
6. composition_items: Array of 3 to 6 key components/analytical constituents with their functional role.
7. instructions_title: 'Feeding Guide' (for pet foods) or 'Instructions for Use' - NO emojis
8. instructions_steps: Array of 3 to 5 practical, numbered instructions.
9. storage_text: Clear storage advice.
10. key_ingredients_flat: Comma-separated list for backend filters.
11. packaging_form: Packaging & physical form.
12. plain_description: 2 concise sentences for POS receipts and sales invoices.
13. search_synonyms: Comma-separated synonyms, pack size variations (e.g. 2kg, 2 kg, 2000g), species/life-stage terms, and manufacturer codes.
14. selected_image_urls: List of up to 3 cleanest high-res manufacturer URLs from candidate images WITHOUT watermarks or retailer logos.

Return strictly a valid JSON object matching this structure.
"""

    def _call_ai_engine(self, context_text, image_candidates):
        """Dispatch to either Google Gemini or OpenAI based on Settings"""
        ir_config = self.env['ir.config_parameter'].sudo()
        provider = ir_config.get_param('stephans_product_ai_enrich.ai_provider') or 'gemini'
        openai_key = (ir_config.get_param('stephans_product_ai_enrich.openai_api_key') or '').strip()
        openai_model = ir_config.get_param('stephans_product_ai_enrich.openai_model') or 'gpt-4o'
        gemini_key = (ir_config.get_param('stephans_product_ai_enrich.gemini_api_key') or '').strip()
        gemini_model = ir_config.get_param('stephans_product_ai_enrich.gemini_model') or 'gemini-2.0-flash'
        if gemini_model in ('gemini-2.5-flash', 'gemini-3.5-flash'):
            gemini_model = 'gemini-2.0-flash'

        if provider == 'gemini':
            if gemini_key:
                _logger.info("Enriching product %s with Google Gemini (%s)", self.name, gemini_model)
                return self._call_gemini(gemini_key, gemini_model, context_text, image_candidates)
            elif openai_key:
                _logger.info("Gemini key not configured; falling back to OpenAI (%s) for %s", openai_model, self.name)
                return self._call_openai(openai_key, openai_model, context_text, image_candidates)
            else:
                raise UserError(
                    "Please configure your Google Gemini API Key or OpenAI API Key in Settings > General Settings > AI Catalog Enricher."
                )
        else:
            if openai_key:
                _logger.info("Enriching product %s with OpenAI (%s)", self.name, openai_model)
                return self._call_openai(openai_key, openai_model, context_text, image_candidates)
            elif gemini_key:
                _logger.info("OpenAI key not configured; falling back to Gemini (%s) for %s", gemini_model, self.name)
                return self._call_gemini(gemini_key, gemini_model, context_text, image_candidates)
            else:
                raise UserError(
                    "Please configure your OpenAI API Key or Google Gemini API Key in Settings > General Settings > AI Catalog Enricher."
                )

    def _clean_json_response(self, raw_text):
        """Helper to safely extract JSON from LLM responses even if wrapped in markdown fences"""
        text = (raw_text or '').strip()
        if text.startswith('```'):
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
        return json.loads(text.strip())

    def _call_gemini(self, api_key, model, context_text, image_candidates):
        """Call Google Gemini API using native Python urllib with clean error handling"""
        endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
        prompt = self._build_catalog_prompt(context_text, image_candidates)

        req_payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1
            }
        }
        data = json.dumps(req_payload).encode('utf-8')
        req = urllib.request.Request(
            endpoint,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                res = json.loads(resp.read().decode('utf-8'))
                raw_text = res['candidates'][0]['content']['parts'][0]['text']
                return self._clean_json_response(raw_text)
        except urllib.error.HTTPError as he:
            err_content = he.read().decode('utf-8', errors='ignore')
            if he.code in (401, 403):
                raise UserError("Google Gemini Authentication Error: Your API key is invalid or unauthorized.")
            elif he.code == 429:
                raise UserError("Google Gemini Quota Exceeded (429): Free tier limits reached for this project.")
            elif he.code == 404:
                raise UserError(f"Google Gemini Model '{model}' not found. Please set model to 'gemini-2.0-flash' in Settings.")
            else:
                raise UserError(f"Google Gemini API error ({he.code}): {err_content}")
        except Exception as e:
            raise UserError(f"Google Gemini API call failed: {e}")

    def _call_openai(self, api_key, model, context_text, image_candidates):
        """Call OpenAI API using native Python urllib with clean error handling"""
        prompt = self._build_catalog_prompt(context_text, image_candidates)
        req_payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a master product catalog enricher. Return only strictly valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "temperature": 0.1
        }
        data = json.dumps(req_payload).encode('utf-8')
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=data,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=35) as resp:
                res_body = json.loads(resp.read().decode('utf-8'))
                content = res_body['choices'][0]['message']['content']
                return self._clean_json_response(content)
        except urllib.error.HTTPError as he:
            err_content = he.read().decode('utf-8', errors='ignore')
            if he.code in (401, 403):
                raise UserError("OpenAI Authentication Error (401): The OpenAI API Key is invalid or has been revoked.")
            elif he.code == 429:
                raise UserError("OpenAI Quota Exceeded (429): You have run out of API credits on your OpenAI account.")
            else:
                raise UserError(f"OpenAI API error ({he.code}): {err_content}")
        except Exception as e:
            raise UserError(f"OpenAI API call failed: {e}")

    def _strip_emojis(self, text):
        """Cleanly strip emojis and decorative symbols from text to maintain professional e-commerce typography"""
        if not text:
            return ""
        clean = re.sub(
            r'[\U00010000-\U0010ffff]|[\u2600-\u27bf]|[\u2300-\u23ff]|[\u2b50-\u2b55]|[\u3030\u303d\u3297\u3299]|[\ufe00-\ufe0f\u200d]',
            '',
            str(text),
        )
        clean = re.sub(r'^\s*[-•·–]\s*', '', clean)
        return clean.strip()

    def _render_stephans_catalog_html(self, data):
        """Render the exact Stephan's Pet Store catalog HTML template formula without emojis"""
        title = self._strip_emojis(data.get('title') or self.name)
        lead = self._strip_emojis(data.get('lead_summary') or '')
        highlights = data.get('key_highlights') or []
        comp_title = self._strip_emojis(data.get('composition_title') or 'Composition & Ingredients')
        comp_items = data.get('composition_items') or []
        inst_title = self._strip_emojis(data.get('instructions_title') or 'Instructions for Use')
        inst_steps = data.get('instructions_steps') or []
        storage = self._strip_emojis(data.get('storage_text') or 'Store in a cool, dry, well-ventilated area away from direct sunlight and humidity.')

        highlights_html = ""
        for hl in highlights:
            if isinstance(hl, dict):
                h_header = self._strip_emojis(hl.get('header', ''))
                h_detail = self._strip_emojis(hl.get('detail', ''))
                highlights_html += f'                    <li class="py-1"><strong>{h_header}:</strong> {h_detail}</li>\n'
            elif isinstance(hl, str):
                cleaned_hl = self._strip_emojis(hl)
                highlights_html += f'                    <li class="py-1">{cleaned_hl}</li>\n'

        comp_html = ""
        for c in comp_items:
            if isinstance(c, dict):
                c_name = self._strip_emojis(c.get('name', ''))
                c_desc = self._strip_emojis(c.get('description', ''))
                if c_desc:
                    comp_html += f'                            <li class="py-1"><strong>{c_name}:</strong> {c_desc}</li>\n'
                else:
                    comp_html += f'                            <li class="py-1"><strong>{c_name}</strong></li>\n'
            elif isinstance(c, str):
                cleaned_c = self._strip_emojis(c)
                comp_html += f'                            <li class="py-1">{cleaned_c}</li>\n'

        inst_html = ""
        for s in inst_steps:
            cleaned_s = self._strip_emojis(s)
            inst_html += f'                            <li class="py-1">{cleaned_s}</li>\n'

        html = f"""<div class="container my-4" style="background: #ffffff;">
    <div class="row">
        <div class="col-12">
            <h3 class="mb-3" style="color: #3e220f; font-weight: 700;">{title}</h3>
            <p class="lead text-muted" style="font-size: 1.05rem; line-height: 1.6;">
                {lead}
            </p>
            
            <div class="mb-4" style="border: 1px solid #e5e7eb; border-radius: 8px; background: #ffffff; padding: 20px; box-shadow: none;">
                <h5 class="mb-3" style="color: #3e220f; font-weight: 700; border-bottom: 1px solid #f3f4f6; padding-bottom: 8px;">Key Product Highlights</h5>
                <ul class="list-unstyled mb-0" style="color: #374151;">
{highlights_html}                </ul>
            </div>

            <div class="row mb-4">
                <div class="col-md-6 mb-3">
                    <div class="h-100" style="border: 1px solid #e5e7eb; border-radius: 8px; background: #ffffff; padding: 20px; box-shadow: none;">
                        <h5 class="mb-3" style="color: #3e220f; font-weight: 700; border-bottom: 1px solid #f3f4f6; padding-bottom: 8px;">{comp_title}</h5>
                        <ul class="mb-0" style="color: #374151; padding-left: 18px;">
{comp_html}                        </ul>
                    </div>
                </div>
                <div class="col-md-6 mb-3">
                    <div class="h-100" style="border: 1px solid #e5e7eb; border-radius: 8px; background: #ffffff; padding: 20px; box-shadow: none;">
                        <h5 class="mb-3" style="color: #3e220f; font-weight: 700; border-bottom: 1px solid #f3f4f6; padding-bottom: 8px;">{inst_title}</h5>
                        <ol class="mb-0" style="color: #374151; padding-left: 18px;">
{inst_html}                        </ol>
                    </div>
                </div>
            </div>

            <div class="mb-3" style="background-color: #f8fafc; border-left: 4px solid #634832; padding: 12px 16px; border-radius: 4px; color: #475569; font-size: 0.95rem;">
                <strong>Storage:</strong> {storage}
            </div>
        </div>
    </div>
</div>"""
        return html

    def _stage_ai_data_for_review(self, data):
        """
        Stage AI-prepared suggestions and candidate images into review fields.
        Nothing is automatically published to storefront name or description until approved.
        """
        rendered_html = self._render_stephans_catalog_html(data)
        _, brand_cfg = self._detect_brand_profile()

        vals = {
            'x_suggested_name': self._strip_emojis(data.get('title') or self.name),
            'x_suggested_description_sale': self._strip_emojis(data.get('plain_description') or ''),
            'x_suggested_description': rendered_html,
            'x_key_ingredients': self._strip_emojis(data.get('key_ingredients_flat') or '') or self.x_key_ingredients,
            'x_packaging_form': self._strip_emojis(data.get('packaging_form') or '') or self.x_packaging_form,
            'x_enrichment_status': 'pending_review',
            'x_is_vet_medicine': bool(brand_cfg and brand_cfg.get('is_vet_medicine', False)),
        }

        ai_synonyms = self._strip_emojis(data.get('search_synonyms') or '')
        if ai_synonyms and not self.x_search_synonyms:
            vals['x_search_synonyms'] = ai_synonyms

        img_urls = data.get('selected_image_urls', [])
        if img_urls:
            manufacturer_name = brand_cfg.get('label') if brand_cfg else (getattr(self, 'product_brand_id', False) and self.product_brand_id.name or '')
            front_url = img_urls[0]
            self._validate_and_process_candidate_image(
                url=front_url,
                role='front',
                manufacturer=manufacturer_name,
            )

            roles = ['back', 'detail', 'lifestyle']
            for idx, extra_url in enumerate(img_urls[1:]):
                role = roles[idx] if idx < len(roles) else 'detail'
                self._validate_and_process_candidate_image(
                    url=extra_url,
                    role=role,
                    manufacturer=manufacturer_name,
                )
            vals['image_quality_status'] = 'pending_review'

        # Strictly enforce store data protection rule before writing
        self._assert_store_data_protected(vals)
        self.write(vals)

    def _recompute_image_quality_status(self):
        """Derive quality status strictly from review records."""
        for product in self:
            reviews = product.image_review_ids
            if not reviews:
                product.image_quality_status = "approved" if product.image_1920 else "uninspected"
            elif any(r.approval_status == "pending_review" for r in reviews):
                product.image_quality_status = "pending_review"
            elif any(r.approval_status == "approved" for r in reviews):
                product.image_quality_status = "approved"
            else:
                product.image_quality_status = "rejected"

    @staticmethod
    def _compute_dhash(img, hash_size=8):
        """Computes a 64-bit difference hash (dHash) for visual perceptual similarity."""
        from PIL import Image
        gray = img.convert("L").resize((hash_size + 1, hash_size), Image.Resampling.LANCZOS)
        pixels = list(gray.getdata())
        diff = []
        for row in range(hash_size):
            for col in range(hash_size):
                left = pixels[row * (hash_size + 1) + col]
                right = pixels[row * (hash_size + 1) + col + 1]
                diff.append(left > right)
        decimal_val = 0
        for index, val in enumerate(diff):
            if val:
                decimal_val |= 1 << index
        return f"{decimal_val:016x}"

    @staticmethod
    def _hamming_distance(hash1, hash2):
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return 99
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        return bin(val1 ^ val2).count("1")

    @staticmethod
    def _encode_webp_target(pil_img, max_kb, qualities=(85, 80, 75, 70, 65, 55)):
        import io
        best_bytes = None
        for q in qualities:
            buf = io.BytesIO()
            pil_img.save(buf, format="WEBP", quality=q, method=6)
            b = buf.getvalue()
            if (len(b) / 1024.0) <= max_kb or q == qualities[-1]:
                best_bytes = b
                break
        return best_bytes, round(len(best_bytes) / 1024.0, 1)

    def _validate_and_process_candidate_image(self, url, role="front", source_type=None, manufacturer=""):
        """
        Hardened Image Quality, Provenance & Multi-Derivative Pipeline:
        1. SSRF Guard: hostname verification, private IP & loopback blocking
        2. 4-Tier Provenance Classification: manufacturer, authorized_distributor, trusted_retailer, external_unverified
        3. Streaming Resource-Capped Download: 12MB limit & image/* Content-Type validation
        4. PIL Decompression Bomb Guard & Dimension Verification (>=1000x1000px floor)
        5. Catalogue-Wide Perceptual Deduplication via 64-bit dHash (Hamming distance <= 4)
        6. Real Foreground Bounding Box Detection: package occupies ~80% of 1:1 canvas
        7. Multi-Tier WebP Derivatives (keeping original raw_image unchanged for gallery zoom):
           - Product-page preview: 1200x1200 WebP (100-250 KB)
           - Product-card image: 480x480 WebP (40-100 KB)
           - Search thumbnail: 160x160 WebP (10-30 KB)
        8. Media Review Staging: 100% human approval required before storefront publication
        """
        import hashlib
        import io
        import ipaddress
        import socket
        from PIL import Image, ImageChops

        if not url or not url.startswith("http"):
            return False

        # 1. SSRF Guard & Hostname Validation
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in ("http", "https") or not parsed.hostname:
            return False

        hostname = parsed.hostname.lower()
        try:
            target_ip = socket.gethostbyname(hostname)
            ip_obj = ipaddress.ip_address(target_ip)
            if ip_obj.is_private or ip_obj.is_loopback or ip_obj.is_reserved or ip_obj.is_link_local:
                _logger.warning("SSRF Block: URL %s resolved to private/loopback IP %s", url, target_ip)
                return False
        except Exception as e:
            _logger.warning("DNS resolution failed for hostname %s: %s", hostname, e)
            return False

        # 2. Strict 4-Tier Domain Provenance Derivation
        derived_source_type, license_note = self._classify_domain_provenance(hostname)

        # Watermark & Marketplace Keyword URL Inspection
        low_url = url.lower()
        blocked_keywords = (
            "watermark", "sample", "preview", "wm_", "stock", "shopee",
            "lazada", "alibaba", "aliexpress", "ebay", "amazon", "temu", "promo", "badge"
        )
        if any(bw in low_url for bw in blocked_keywords):
            _logger.info("Blocked image candidate %s: watermark/marketplace keyword detected", url)
            return False

        # 3. Streaming Download with 12MB limit & Content-Type check
        raw_bytes = None
        try:
            req = urllib.request.Request(
                url,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) StephanPetStore/2.0"},
            )
            with urllib.request.urlopen(req, timeout=12) as resp:
                content_type = resp.headers.get("Content-Type", "").lower()
                if not any(t in content_type for t in ("image/jpeg", "image/png", "image/webp", "image/jpg")):
                    return False

                chunks = []
                total_size = 0
                MAX_BYTES = 12 * 1024 * 1024
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    chunks.append(chunk)
                    total_size += len(chunk)
                    if total_size > MAX_BYTES:
                        return False
                raw_bytes = b"".join(chunks)
        except Exception as e:
            _logger.warning("Could not download candidate image %s: %s", url, e)
            return False

        if not raw_bytes or len(raw_bytes) < 5000:
            return False

        # Checksum & Exact File Deduplication
        checksum = hashlib.sha256(raw_bytes).hexdigest()
        existing_review = self.env["product.image.review"].sudo().search([
            ("file_checksum", "=", checksum),
        ], limit=1)
        if existing_review:
            return False

        # 4. PIL Decompression Bomb Guard & Dimension Verification (>=1000x1000 floor)
        try:
            Image.MAX_IMAGE_PIXELS = 50_000_000
            img = Image.open(io.BytesIO(raw_bytes))
            img.load()
            orig_w, orig_h = img.size
        except Exception:
            return False

        if orig_w < 1000 or orig_h < 1000:
            _logger.info("Blocked image %s: resolution %sx%s is below minimum 1000x1000 threshold", url, orig_w, orig_h)
            return False

        aspect = round(orig_w / float(orig_h), 2)

        # 5. Catalogue-Wide Perceptual Hashing (dHash) Deduplication
        dhash_val = self._compute_dhash(img)
        existing_hashes = self.env["product.image.review"].sudo().search_read(
            [("phash", "!=", False)], ["id", "phash", "product_tmpl_id"]
        )
        for rec in existing_hashes:
            if self._hamming_distance(dhash_val, rec["phash"]) <= 4:
                return False

        # 6. Real Foreground Bounding Box Detection & 80% Canvas Occupancy
        is_transparent = img.mode in ("RGBA", "LA") or (img.mode == "P" and "transparency" in img.info)
        if is_transparent:
            rgba_img = img.convert("RGBA")
            bbox = rgba_img.getbbox()
        else:
            rgb_img = img.convert("RGB")
            bg = Image.new("RGB", rgb_img.size, (255, 255, 255))
            diff = ImageChops.difference(rgb_img, bg)
            mask = diff.convert("L").point(lambda p: 255 if p > 18 else 0)
            bbox = mask.getbbox()

        if not bbox or (bbox[2] - bbox[0] < 100) or (bbox[3] - bbox[1] < 100):
            bbox = (0, 0, orig_w, orig_h)

        product_crop = img.crop(bbox)
        fg_w = bbox[2] - bbox[0]
        fg_h = bbox[3] - bbox[1]

        # Product-page preview master square canvas: 1200x1200 px
        canvas_dim = 1200
        target_fg_max = int(canvas_dim * 0.80)
        scale = target_fg_max / float(max(fg_w, fg_h))
        new_w = max(1, int(fg_w * scale))
        new_h = max(1, int(fg_h * scale))
        scaled_crop = product_crop.resize((new_w, new_h), Image.Resampling.LANCZOS)
        measured_occupancy = round((max(new_w, new_h) / float(canvas_dim)) * 100.0, 1)

        canvas_1200 = Image.new("RGB", (canvas_dim, canvas_dim), (255, 255, 255))
        offset = ((canvas_dim - new_w) // 2, (canvas_dim - new_h) // 2)
        if scaled_crop.mode in ("RGBA", "LA"):
            canvas_1200.paste(scaled_crop, offset, scaled_crop.convert("RGBA"))
        else:
            canvas_1200.paste(scaled_crop, offset)

        # 7. Generate Separate Multi-Tier WebP Derivatives:
        # (a) Product-page preview: 1200x1200 WebP (target <= 250 KB)
        webp_1200_bytes, filesize_1200_kb = self._encode_webp_target(canvas_1200, max_kb=250)

        # (b) Product-card image: 480x480 WebP (target 40-100 KB)
        canvas_480 = canvas_1200.resize((480, 480), Image.Resampling.LANCZOS)
        webp_480_bytes, filesize_480_kb = self._encode_webp_target(canvas_480, max_kb=95)

        # (c) Search thumbnail: 160x160 WebP (target 10-30 KB)
        canvas_160 = canvas_1200.resize((160, 160), Image.Resampling.LANCZOS)
        webp_160_bytes, filesize_160_kb = self._encode_webp_target(canvas_160, max_kb=28)

        # 8. Stage into product.image.review queue (100% human approval required)
        review_vals = {
            "product_tmpl_id": self.id,
            "original_source_url": url,
            "verified_domain": hostname,
            "source_type": derived_source_type,
            "manufacturer_name": manufacturer or (getattr(self, 'product_brand_id', False) and self.product_brand_id.name or ""),
            "download_date": fields.Datetime.now(),
            "original_width": orig_w,
            "original_height": orig_h,
            "aspect_ratio": aspect,
            "foreground_coverage_pct": measured_occupancy,
            "file_checksum": checksum,
            "phash": dhash_val,
            "image_role": role,
            "approval_status": "pending_review",
            "raw_image": base64.b64encode(raw_bytes),
            "webp_image": base64.b64encode(webp_1200_bytes),
            "webp_filesize_kb": filesize_1200_kb,
            "webp_card_480": base64.b64encode(webp_480_bytes),
            "webp_card_480_kb": filesize_480_kb,
            "webp_thumb_160": base64.b64encode(webp_160_bytes),
            "webp_thumb_160_kb": filesize_160_kb,
            "usage_license_note": license_note,
        }
        self.env["product.image.review"].sudo().create(review_vals)
        self._recompute_image_quality_status()
        _logger.info(
            "Staged image asset for %s [%s]: %sx%s, preview=%sKB, card480=%sKB, thumb160=%sKB",
            self.name, derived_source_type, orig_w, orig_h, filesize_1200_kb, filesize_480_kb, filesize_160_kb
        )
        return True
