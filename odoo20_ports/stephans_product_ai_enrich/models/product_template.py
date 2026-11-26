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
    "tropicat.pl",
    "tropidog.eu",
    "tropidog.pl",
    "tropical.pl",
    "w.tropical.pl",
    "tropifit.eu",
    "tropifit.pl",
    "josera.com",
    "shop.josera.com",
    "bravecto.com",
    "nexgard.com",
    "elanco.com",
    "f10products.co.uk",
    "whiskas.com",
    "whiskas.in",
    "whiskas.co.uk",
    "whiskas.co.za",
    "mars.com",
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
    "vetpetsmz.com",
    "amazon.ae",
    "amazon.com",
    "amazon.co.uk",
    "petlebi.com",
    "roslinyakwariowe.pl",
    "sklep.roslinyakwariowe.pl",
    "checkers.co.za",
    "epetstore.co.za",
    "aquapet.co.ke",
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
            'https://tropicat.pl/en/products/',
            'https://tropical.pl/en/',
        ],
        'trusted_retailer_urls': [],
        'search_templates': [
            'https://tropicat.pl/en/?s={query}',
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
            'https://tropidog.pl/en/products/',
            'https://tropical.pl/en/',
        ],
        'trusted_retailer_urls': [],
        'search_templates': [
            'https://tropidog.pl/en/?s={query}',
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
            'https://tropifit.pl/en/products/',
            'https://tropical.pl/en/',
        ],
        'trusted_retailer_urls': [],
        'search_templates': [
            'https://tropifit.pl/en/?s={query}',
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
        'tier': 1,
        'official_urls': [
            'https://www.whiskas.in/',
            'https://www.whiskas.com/',
            'https://www.whiskas.co.uk/',
            'https://www.whiskas.co.za/',
        ],
        'trusted_retailer_urls': [
            'https://www.checkers.co.za/',
            'https://www.epetstore.co.za/',
            'https://aquapet.co.ke/',
        ],
        'search_templates': [
            'https://www.whiskas.in/our-products?query={query}',
        ],
        'keywords': 'Whiskas, Mars Petcare, complete wet cat food, adult cat tuna in jelly, crude protein, taurine, zinc',
        'synonyms': 'Whiskas, Whiskas cat pouch, adult wet cat food',
        'guidelines': (
            'Official Whiskas Cat Food. Amazon mobile-first copywriting: highlight flavor, life-stage nutrition, '
            'guaranteed analytical constituents, and exact daily feeding guide formatted with uppercase headlines and line breaks.'
        ),
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
        """Match this product against the Official Brand Catalog Brain (preventing false accessory collisions)."""
        self.ensure_one()
        raw_name = (self.name or '').lower()
        haystack = raw_name
        if hasattr(self, 'product_brand_id') and self.product_brand_id and self.product_brand_id.name:
            haystack += ' ' + self.product_brand_id.name.lower()
        if hasattr(self, 'brand_id') and self.brand_id and self.brand_id.name:
            haystack += ' ' + self.brand_id.name.lower()

        # Guard against false brand assignment when an accessory title merely mentions a food brand (e.g. "Ceramic Pet Bowl With Whiskas")
        accessory_nouns = ('bowl', 'ceramic', 'feeder', 'fountain', 'collar', 'leash', 'harness', 'bed', 'cushion', 'cage', 'carrier')
        food_or_vet_only_brands = {'whiskas', 'summit', 'josera', 'ownat', 'tropidog', 'tropicat', 'tropifit', 'bravecto', 'nexgard', 'milbemax', 'f10'}
        has_accessory_noun = any(re.search(rf'\b{noun}\b', raw_name) for noun in accessory_nouns)

        for key, profile in OFFICIAL_BRAND_CATALOG_BRAIN.items():
            if key in haystack:
                if has_accessory_noun and key in food_or_vet_only_brands:
                    continue
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

    def _extract_core_product_query(self):
        """Extract clean product search term without brand name, SKU, or pack size units."""
        self.ensure_one()
        _, profile = self._detect_brand_profile()
        raw = re.sub(r'\[[^\]]+\]', ' ', (self.name or ''))
        if profile:
            b_label = profile.get('label', '')
            raw = re.sub(re.escape(b_label), ' ', raw, flags=re.IGNORECASE)
            for b_key in FLAGSHIP_BRAND_KEYS:
                raw = re.sub(rf'\b{re.escape(b_key)}\b', ' ', raw, flags=re.IGNORECASE)
        # Strip pack sizes like 200mls, 200ml, 2kg, 3kg, 10kg, 60 capsules, 40pcs
        raw = re.sub(r'\b\d+(?:\.\d+)?\s*(?:kg|g|l|ml|mls|pcs|capsules|tablets)\b', ' ', raw, flags=re.IGNORECASE)
        raw = re.sub(r'\b(?:s-item\d+|item-\d+)\b', ' ', raw, flags=re.IGNORECASE)
        raw = re.sub(r'[^a-zA-Z0-9\s]', ' ', raw)
        words = [w for w in raw.split() if len(w) >= 2]
        return ' '.join(words[:5]).strip()

    def _build_official_seed_urls(self):
        """Build official brand Tier-1 manufacturer search + product URLs + Tier-2 cross-check URLs."""
        self.ensure_one()
        _, profile = self._detect_brand_profile()
        clean_name = re.sub(r'\s+', ' ', (self.name or '').strip())
        core_query = self._extract_core_product_query() or ' '.join(clean_name.split()[:4])
        encoded_core = urllib.parse.quote_plus(core_query)
        short_query = ' '.join(clean_name.split()[:4])
        encoded_short = urllib.parse.quote_plus(short_query)

        urls = []
        if profile:
            # Put targeted search templates first so _fetch_catalog_sources discovers the exact product detail page
            for tmpl in profile.get('search_templates', []):
                u_core = tmpl.format(query=encoded_core)
                if u_core not in urls:
                    urls.append(u_core)
                u_short = tmpl.format(query=encoded_short)
                if u_short not in urls:
                    urls.append(u_short)
            for u in profile.get('official_urls', []):
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
                and 'tropidog.eu' not in u
                and 'tropicat.eu' not in u
                and 'tropifit.eu' not in u
                and 'vetforest.com/products/bioline-tofu' not in u
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

        # Ensure clean core search URLs are always seeded first so official product detail pages are discovered
        if 'litter' not in (self.name or '').lower() or not self.x_source_urls:
            self.action_seed_official_brand_urls()

        # 1. Fetch & parse content from Tier-1 manufacturer & Tier-2 cross-check URLs
        scraped_text, image_candidates, image_context = self._fetch_catalog_sources()

        # 2. Query AI Engine
        ai_data = self._call_ai_engine(scraped_text, image_candidates)

        # 3. Validate Error-Prevention Gates (Brand, Pack Size, Species, Life Stage)
        self._validate_enrichment_gates(ai_data)

        # 4. Stage outputs into review fields (manual review queue only; zero automatic publishing)
        self._stage_ai_data_for_review(
            ai_data,
            image_candidates=image_candidates,
            image_context=image_context,
        )

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
                    "Product '%s' suggestions and candidate packshots staged into the Review Queue. Human verification required before publishing."
                ) % self.name,
                'type': 'success',
                'sticky': False,
            }
        }

    def _archive_raw_text_before_update(self):
        """
        Automated Rollback Backup:
        Every product's original raw text, name, and descriptions are archived in scripts/backups/
        before any AI or catalogue update runs.
        """
        import os
        import json
        from datetime import datetime

        # Candidate backup locations (supporting local workspace, server addons, and system backup path)
        possible_dirs = [
            "/opt/odoo/backups/products",
            "/opt/odoo/odoo20-addons/scripts/backups",
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts", "backups")),
            os.path.abspath(os.path.join(os.getcwd(), "scripts", "backups")),
        ]

        target_dir = None
        for p in possible_dirs:
            try:
                os.makedirs(p, exist_ok=True)
                if os.access(p, os.W_OK):
                    target_dir = p
                    break
            except Exception:
                continue

        if not target_dir:
            target_dir = "/tmp/odoo20_product_backups"
            os.makedirs(target_dir, exist_ok=True)

        for rec in self:
            sku = (rec.default_code or f"ID_{rec.id}").strip()
            safe_sku = "".join(c for c in sku if c.isalnum() or c in ("-", "_"))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:19]

            def _extract_val(val):
                if isinstance(val, dict):
                    return val
                return str(val) if val is not None else ""

            backup_data = {
                "product_id": rec.id,
                "sku": rec.default_code or "",
                "name": _extract_val(rec.name),
                "timestamp": timestamp,
                "backup_date_iso": datetime.now().isoformat(),
                "description_sale": _extract_val(rec.description_sale),
                "website_description": _extract_val(rec.website_description),
                "x_enrichment_status": rec.x_enrichment_status or "",
                "list_price": rec.list_price,
                "standard_price": rec.standard_price,
            }

            filename = f"backup_{rec.id}_{safe_sku}_{timestamp}.json"
            backup_path = os.path.join(target_dir, filename)

            try:
                with open(backup_path, "w", encoding="utf-8") as f:
                    json.dump(backup_data, f, indent=2, ensure_ascii=False)
                _logger.info("Automated Rollback Backup saved for Product [%s] %s to %s", rec.id, rec.name, backup_path)
            except Exception as e:
                _logger.warning("Could not write rollback backup for product %s: %s", rec.id, e)

    def action_rollback_to_backup(self, backup_file=None):
        """
        One-click Rollback:
        Restores this product's description, name, and attributes from the latest (or specified) backup file.
        """
        self.ensure_one()
        import os
        import json
        import glob

        search_dirs = [
            "/opt/odoo/backups/products",
            "/opt/odoo/odoo20-addons/scripts/backups",
            os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "scripts", "backups")),
            os.path.abspath(os.path.join(os.getcwd(), "scripts", "backups")),
            "/tmp/odoo20_product_backups"
        ]

        if not backup_file:
            pattern = f"backup_{self.id}_*.json"
            candidates = []
            for sdir in search_dirs:
                if os.path.exists(sdir):
                    candidates.extend(glob.glob(os.path.join(sdir, pattern)))

            if not candidates:
                raise UserError(_("No backup files found for Product [%s] in backup directories.") % self.id)

            candidates.sort(key=os.path.getmtime, reverse=True)
            backup_file = candidates[0]

        if not os.path.exists(backup_file):
            raise UserError(_("Specified backup file does not exist: %s") % backup_file)

        with open(backup_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        restore_vals = {}
        if "website_description" in data:
            restore_vals["website_description"] = data["website_description"]
        if "description_sale" in data:
            restore_vals["description_sale"] = data["description_sale"]
        if "name" in data and isinstance(data["name"], str):
            restore_vals["name"] = data["name"]

        self._assert_store_data_protected(restore_vals)
        self.sudo().write(restore_vals)
        _logger.info("Product [%s] rolled back successfully from %s", self.id, backup_file)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Product Rolled Back Successfully'),
                'message': _('Restored descriptions from backup archive: %s') % os.path.basename(backup_file),
                'type': 'success',
                'sticky': False,
            }
        }

    def _auto_publish_staged_enrichment_and_media(self):
        """
        Publishes validated text description suggestions to the product after human approval.
        Media review assets remain strictly in the manual review queue (pending_review)
        for individual human inspection and approval.
        """
        # Automated Rollback Backup: Archive raw text before any update runs
        self._archive_raw_text_before_update()

        for rec in self:
            pub_vals = {
                'x_enrichment_status': 'approved',
            }
            if rec.x_suggested_description:
                pub_vals['website_description'] = rec.x_suggested_description
            if rec.x_suggested_description_sale:
                pub_vals['description_sale'] = rec.x_suggested_description_sale

            self._assert_store_data_protected(pub_vals)
            rec.sudo().write(pub_vals)

            # Strict manual review boundary: Images are NEVER automatically approved or published.
            # All candidate assets remain in product.image.review (pending_review) for human review.
            _logger.info("Product [%s] descriptions published; image reviews held in pending_review for manual approval.", rec.id)

            rec._recompute_image_quality_status()
            rec._invalidate_product_shared_cache()

    def action_approve_ai_enrichment(self):
        """
        Approve & publish both staged description suggestions and all pending official images.
        """
        if not self.env.user.has_group("stephans_product_ai_enrich.group_media_reviewer") and not self.env.is_admin():
            raise AccessError(_("Permission Denied: Only authorized Catalog Reviewers can approve product enrichment."))

        self._auto_publish_staged_enrichment_and_media()

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Enrichment & 3 Official Images Approved & Published'),
                'message': _('Approved description and 3 official images have been published and search cache updated.'),
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
    def cron_auto_enrich_products(self, limit=10):
        """
        Controlled Batch Enrich (Default limit=10 products per batch).
        Auto-enriches and publishes up to 10 products (text + 3 official images) per batch.
        """
        limit = min(int(limit or 10), 20)
        ir_config = self.env['ir.config_parameter'].sudo()
        gemini_key = (ir_config.get_param('stephans_product_ai_enrich.gemini_api_key') or '').strip()
        openai_key = (ir_config.get_param('stephans_product_ai_enrich.openai_api_key') or '').strip()
        if not gemini_key and not openai_key:
            _logger.info("AI Batch Enrich skipped: No Gemini or OpenAI API key configured.")
            return True

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
            # Second pass: backfill any previously text-enriched products that haven't received their 3 official images yet
            backfill_domain = [
                ('active', '=', True),
                ('sale_ok', '=', True),
                ('x_ai_last_error', '=', False),
                ('image_review_ids', '=', False),
            ]
            batch = self.search(
                backfill_domain + flagship_or,
                order='is_published desc, list_price desc, id asc',
                limit=limit,
            )
            if len(batch) < limit:
                extra_bf = self.search(
                    backfill_domain + [('id', 'not in', batch.ids)],
                    order='is_published desc, list_price desc, id asc',
                    limit=limit - len(batch),
                )
                batch |= extra_bf

        if not batch:
            _logger.info("AI Batch Enrich: No unenriched products remaining.")
            return True

        _logger.info("AI Batch Enrich: Auto-enriching & publishing batch of %d products (text + 3 official images): %s", len(batch), batch.mapped('name'))
        for product in batch:
            try:
                product.action_seed_official_brand_urls()
                product.action_regenerate_ai_details()
                self.env.cr.commit()
                _logger.info("AI Batch Enrich: Enriched & published [%s] %s with 3 official images", product.id, product.name)
            except Exception as e:
                self.env.cr.rollback()
                err_msg = str(e)[:500]
                _logger.warning("AI Batch Enrich: Failed on [%s] %s: %s", product.id, product.name, err_msg)
                if not any(code in err_msg for code in ('401', '403', '429', 'configure your')):
                    product.write({'x_ai_last_error': err_msg})
                    self.env.cr.commit()
                else:
                    break
        return True

    def _is_candidate_image_filename_compatible(self, url):
        """
        Reject candidate image URLs whose filename/path is a promotional banner, blog image,
        popup, newsletter, magazine advert, homepage graphic, or names a conflicting flavor/protein
        or species from a "Related Products" carousel.
        """
        if not url:
            return False
        parsed = urllib.parse.urlparse(url)
        unquoted_path = urllib.parse.unquote(parsed.path).lower()
        fname = unquoted_path.rsplit('/', 1)[-1]
        prod_lower = (self.name or '').lower()

        # 0. Strict Blocklist against Banners, Blogs, Popups, Adverts, and Generic UI assets
        non_product_patterns = (
            'baner', 'banner', 'fotos-blog', 'fotos_blog', '/blog/', 'popup',
            'newsletter', 'advert', 'vet-times', 'mobile_homepage', 'homepage',
            'about.jpg', 'dogs_selector', 'q@3x', 'q%403x', 'q%25403x', 'mask2014',
            'adult-nutrition.png',
        )
        if any(pat in unquoted_path or pat in url.lower() for pat in non_product_patterns):
            return False

        # 1. Prevent conflicting protein / flavor packshots
        flavors = ('chicken', 'lamb', 'salmon', 'fish', 'turkey', 'beef', 'duck', 'rabbit', 'venison', 'pork', 'tuna')
        prod_flavors = {f for f in flavors if re.search(rf'\b{f}\b', prod_lower)}
        if prod_flavors:
            url_flavors = {f for f in flavors if f in fname}
            if url_flavors and not url_flavors.intersection(prod_flavors):
                return False

        # 2. Prevent conflicting species / life-stage packshots in filename
        species_conflicts = [
            ('dog', ('cat', 'kitten', 'feline')),
            ('puppy', ('cat', 'kitten', 'adult', 'senior')),
            ('cat', ('dog', 'puppy', 'canine')),
            ('kitten', ('dog', 'puppy', 'adult', 'senior')),
            ('adult', ('puppy', 'kitten', 'junior')),
        ]
        for token, forbidden in species_conflicts:
            if re.search(rf'\b{token}\b', prod_lower) and not any(re.search(rf'\b{fb}\b', prod_lower) for fb in forbidden):
                if any(re.search(rf'(?:^|[\-_ ]){fb}(?:[\-_ .]|$)', fname) for fb in forbidden):
                    return False

        return True

    def _verify_three_identifier_product_match(self, url):
        """
        Verify at least 3 product identifiers before allowing automatic approval of an external image:
        1. Brand Identifier (verified brand profile matches domain and is not an accessory collision)
        2. Exact Product Title / Formulation Identifier (filename/path matches core formulation tokens or official catalog item code, and passes banner/blog/popup check)
        3. Weight / Volume / Pack Count OR Manufacturer SKU / EAN Identifier
        """
        self.ensure_one()
        if not url or not self._is_candidate_image_filename_compatible(url):
            return False

        parsed = urllib.parse.urlparse(url)
        hostname = (parsed.hostname or '').lower()
        source_tier, _ = self._classify_domain_provenance(hostname)
        if source_tier != 'manufacturer':
            return False

        # Identifier 1: Brand Match
        brand_key, profile = self._detect_brand_profile()
        if not brand_key or not profile:
            return False

        unquoted_url = urllib.parse.unquote(url).lower()
        prod_lower = (self.name or '').lower()

        # Identifier 2: Formulation / Title Token or Verified Catalog Item Code
        stop_words = {
            'with', 'for', 'and', 'the', 'dog', 'dogs', 'cat', 'cats', 'pet', 'pets',
            'food', 'adult', 'small', 'medium', 'large', 'breeds', 'breed', 'bag',
            'rich', 'whole', 'choice', 'premium', 'super', 'item', brand_key,
        }
        core_tokens = [w for w in re.findall(r'[a-z]{3,}', prod_lower) if w not in stop_words]
        matched_tokens = [w for w in core_tokens if w in unquoted_url]
        has_catalog_code = bool(re.search(r'/(?:2\d{3}[\-_]\d|16[56]\d{10,})', unquoted_url))
        if not matched_tokens and not has_catalog_code:
            return False

        # Identifier 3: Weight / Volume / Pack Count OR Barcode/EAN OR Verified Catalog Code
        size_matches = list(re.finditer(r'\b(\d+(?:\.\d+)?)\s*(kg|g|ml|mls|l|pcs|pc|tablets|capsules)\b', prod_lower))
        url_compact = re.sub(r'[\-_%\s]+', '', unquoted_url)
        if self.barcode and self.barcode.lower() in url_compact:
            return True
        if has_catalog_code:
            return True
        if size_matches:
            expected_sizes = [f"{m.group(1)}{m.group(2).lower().rstrip('s')}" for m in size_matches]
            if any(sz in url_compact or sz.replace('.', '') in url_compact for sz in expected_sizes):
                return True
            # If the URL explicitly names a DIFFERENT pack size (e.g. 25kg or 15kg when product is 3kg), reject auto-approval
            other_sizes = [
                f"{m.group(1)}{m.group(2).lower().rstrip('s')}"
                for m in re.finditer(r'(\d+(?:\.\d+)?)\s*(kg|g|ml|l)\b', unquoted_url)
            ]
            if other_sizes and not any(osz in expected_sizes for osz in other_sizes):
                return False
            # Require at least 2 matched core formulation tokens if pack size is not encoded in the filename
            return len(matched_tokens) >= 2

        return len(matched_tokens) >= 2

    def _extract_images_from_soup(self, soup, parsed):
        """Extract clean full-resolution product image URLs from a BeautifulSoup document."""
        found = []
        blocked_tokens = (
            'logo', 'icon', 'badge', 'payment', 'watermark', 'banner', 'thumb',
            'avatar', 'flag', 'bsci', 'iso', 'brc', 'fda', 'appa', 'ics',
            'shutterstock', 'oip-c', 'line-1', 'line-curva', '.svg', 'placeholder',
            'favicon', 'header', 'footer', 'wechat', 'whatsapp', 'facebook', 'instagram',
        )
        # Strip related/upsell product blocks before extracting images so we only collect THIS product's official gallery
        for rel_block in soup.select('.related, .upsells, .cross-sells, .related-products, section.related'):
            rel_block.decompose()

        for img in soup.find_all('img'):
            raw_candidates = [
                img.get('data-large_image'),
                img.get('data-zoom-image'),
                img.get('data-full-url'),
                img.get('data-src'),
                img.get('src'),
            ]
            for src in raw_candidates:
                if not src or not isinstance(src, str):
                    continue
                src = src.strip()
                if src.startswith('data:'):
                    continue
                if src.startswith('//'):
                    src = 'https:' + src
                elif src.startswith('/'):
                    src = f"{parsed.scheme}://{parsed.netloc}{src}"
                elif not src.startswith('http'):
                    src = urllib.parse.urljoin(f"{parsed.scheme}://{parsed.netloc}/", src)

                src_lower = src.lower()
                if any(b in src_lower for b in blocked_tokens):
                    continue
                if not self._is_candidate_image_filename_compatible(src):
                    continue

                # Strip WordPress (-300x300.jpg) & Shopify (_600x600.jpg) thumbnail suffixes to obtain full-res original
                full_res_src = re.sub(r'-\d+x\d+(\.[a-zA-Z]{3,4})(?:\?.*)?$', r'\1', src)
                full_res_src = re.sub(r'_\d+x\d*\.', '.', full_res_src)
                full_res_src = re.sub(r'width=\d+', 'width=1920', full_res_src)

                if full_res_src.startswith('http') and full_res_src not in found:
                    found.append(full_res_src)
                if src.startswith('http') and src != full_res_src and src not in found:
                    found.append(src)
        return found

    def _extract_image_context_from_soup(self, soup, parsed, identity_page_url):
        """Return accepted image URLs with their verified page and useful HTML metadata."""
        context = {}
        accepted = set(self._extract_images_from_soup(soup, parsed))
        for img in soup.find_all('img'):
            metadata = ' '.join(filter(None, [
                img.get('alt'), img.get('title'), img.get('aria-label'),
                ' '.join(img.get('class') or []),
            ]))[:500]
            for raw in (img.get('data-large_image'), img.get('data-zoom-image'),
                        img.get('data-full-url'), img.get('data-src'), img.get('src')):
                if not raw or not isinstance(raw, str):
                    continue
                src = urllib.parse.urljoin(identity_page_url, raw.strip())
                full_res = re.sub(r'-\d+x\d+(\.[a-zA-Z]{3,4})(?:\?.*)?$', r'\1', src)
                full_res = re.sub(r'_\d+x\d*\.', '.', full_res)
                full_res = re.sub(r'width=\d+', 'width=1920', full_res)
                for candidate in (full_res, src):
                    if candidate in accepted:
                        context[candidate] = {
                            'identity_page_url': identity_page_url,
                            'source_metadata': metadata,
                        }
        return context

    def _discover_product_detail_links(self, soup, base_url, parsed):
        """
        Discover official product detail links on a manufacturer search or catalog page
        that match the current product's core keywords.
        """
        core_query = (self._extract_core_product_query() or '').lower()
        core_tokens = [t for t in re.split(r'\s+', core_query) if len(t) >= 3]
        if not core_tokens:
            return []

        skip_segments = (
            '/tag/', '/category/', '/blog/', '/news/', '/about', '/contact',
            '/cart', '/checkout', '/account', '/login', '/privacy', '/terms',
            'why-you-should', 'how-to-', 'wp-json', 'feed', '.pdf', '.jpg', '.png',
            '?s=', 'search?q=', '#', 'javascript:', 'mailto:', 'tel:',
        )
        scored_links = []
        seen_hrefs = set()

        for a_tag in soup.find_all('a', href=True):
            href = (a_tag.get('href') or '').strip()
            if not href:
                continue
            if href.startswith('//'):
                href = 'https:' + href
            elif href.startswith('/'):
                href = f"{parsed.scheme}://{parsed.netloc}{href}"
            elif not href.startswith('http'):
                href = urllib.parse.urljoin(base_url, href)

            href_clean = href.split('#')[0].strip()
            if not href_clean or href_clean == base_url or href_clean in seen_hrefs:
                continue

            href_parsed = urllib.parse.urlparse(href_clean)
            if not href_parsed.hostname or href_parsed.hostname.lower() != (parsed.hostname or '').lower():
                continue

            low_href = href_clean.lower()
            if any(seg in low_href for seg in skip_segments):
                continue

            anchor_text = (a_tag.get_text(' ', strip=True) or '').lower()
            slug_text = urllib.parse.unquote(href_parsed.path).lower().replace('-', ' ').replace('_', ' ')
            combined_hay = f"{anchor_text} {slug_text}"

            matched_tokens = sum(1 for tok in core_tokens if tok in combined_hay)
            if matched_tokens == 0:
                continue

            score = matched_tokens * 10
            # Exact phrase bonus
            if core_query and core_query in combined_hay:
                score += 25
            # Product URL structure bonus
            if low_href.endswith('.html') or '/product/' in low_href or '/products/' in low_href:
                score += 12

            seen_hrefs.add(href_clean)
            scored_links.append((score, href_clean))

        scored_links.sort(key=lambda item: item[0], reverse=True)
        return [link for _, link in scored_links[:2]]

    def _fetch_catalog_sources(self):
        """Fetch raw HTML, text and high-res clean images from seeded URLs (including 2-hop product detail discovery)."""
        urls = [u.strip() for u in (self.x_source_urls or '').split('\n') if u.strip().startswith('http')]
        combined_text = (
            f"Current Product Name: {self.name}\n"
            f"Default SKU: {self.default_code or ''}\n"
            f"Structured Queries:\n{self.x_structured_queries or ''}\n"
            f"User Target Keywords: {self.x_keywords or ''}\n"
            f"Search Synonyms: {self.x_search_synonyms or ''}\n\n"
        )
        image_candidates = []
        detail_page_images = []
        image_context = {}
        visited_urls = set()
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        for url in urls:
            if url in visited_urls:
                continue
            visited_urls.add(url)
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

                    # 1. Discover official product detail links BEFORE decomposing layout tags
                    discovered_details = []
                    if source_tier in ('manufacturer', 'authorized_distributor'):
                        discovered_details = self._discover_product_detail_links(soup, url, parsed)

                    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'svg']):
                        tag.decompose()

                    text = soup.get_text(' ', strip=True)[:3500]
                    combined_text += f"\n--- Source URL ({source_tier.upper()}): {url} ---\n{text}\n"

                    # 2. Follow discovered official product detail pages (Priority #1 for official 3-angle product galleries)
                    for detail_url in discovered_details:
                        if detail_url in visited_urls:
                            continue
                        visited_urls.add(detail_url)
                        try:
                            d_parsed = urllib.parse.urlparse(detail_url)
                            d_req = urllib.request.Request(detail_url, headers=headers)
                            with urllib.request.urlopen(d_req, timeout=8) as d_resp:
                                d_html = d_resp.read().decode('utf-8', errors='ignore')
                                d_soup = BeautifulSoup(d_html, 'html.parser')
                                for d_tag in d_soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'svg']):
                                    d_tag.decompose()
                                d_text = d_soup.get_text(' ', strip=True)[:4000]
                                combined_text += f"\n--- Official Product Detail Page ({source_tier.upper()}): {detail_url} ---\n{d_text}\n"
                                detail_context = self._extract_image_context_from_soup(
                                    d_soup, d_parsed, detail_url,
                                )
                                image_context.update(detail_context)
                                for d_img in detail_context:
                                    if d_img not in detail_page_images:
                                        detail_page_images.append(d_img)
                        except Exception as de:
                            _logger.debug("Detail page fetch skipped for %s: %s", detail_url, de)

                    # 3. Collect candidate images from manufacturer or authorized_distributor page
                    if source_tier in ('manufacturer', 'authorized_distributor'):
                        for img_url in self._extract_images_from_soup(soup, parsed):
                            if img_url not in image_candidates:
                                image_candidates.append(img_url)

            except Exception as e:
                _logger.warning("Error fetching catalog source %s: %s", url, e)

        # Prioritize images extracted directly from the matched official product detail page
        ordered_candidates = []
        for candidate in detail_page_images + image_candidates:
            if candidate not in ordered_candidates:
                ordered_candidates.append(candidate)

        limited_candidates = ordered_candidates[:15]
        return combined_text, limited_candidates, {
            url: image_context[url] for url in limited_candidates if url in image_context
        }

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
- AMAZON MOBILE-FIRST COPYWRITING STANDARD:
  * Headline Formula: "[Brand] [Product Name] [Size]: [Core Customer Outcome in 6 to 10 words] ([Key Spec])". NEVER use em dashes (—). Always use a clean colon (:) after the product name. Deliver the biggest outcome in the first 8 words.
  * Exactly 5 Feature Bullets in key_highlights: Each "header" MUST be 2 to 4 capitalized words (e.g. "STRENGTHENS LEAN MUSCLES & VITALITY", "SHINY COAT & HYDRATION SUPPORT"). "detail" MUST deliver the immediate tangible outcome, followed by the formulation mechanism.
1. title: Clean, standardized format preserving the exact pack size: [Brand] [Product Line / Feature] [Size or Weight]
2. barcode: Manufacturer EAN-13 or UPC barcode if verified (or empty string).
3. lead_summary: Mobile headline formula: [Brand] [Product Name] [Size]: [Core Customer Outcome in 6 to 10 words] ([Key Spec]). No em dashes (—).
4. key_highlights: Exactly 5 Amazon-style highlights, each with an uppercase bold header and outcome-first detail explanation.
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
        """Dispatch to Google Gemini (with multi-model cascade) or OpenAI, with Brand Brain fallback."""
        ir_config = self.env['ir.config_parameter'].sudo()
        provider = ir_config.get_param('stephans_product_ai_enrich.ai_provider') or 'gemini'
        openai_key = (ir_config.get_param('stephans_product_ai_enrich.openai_api_key') or '').strip()
        openai_model = ir_config.get_param('stephans_product_ai_enrich.openai_model') or 'gpt-4o-mini'
        gemini_key = (ir_config.get_param('stephans_product_ai_enrich.gemini_api_key') or '').strip()
        gemini_model = ir_config.get_param('stephans_product_ai_enrich.gemini_model') or 'gemini-3.6-flash'
        if gemini_model in ('gemini-1.5-flash', 'gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-3.5-flash'):
            gemini_model = 'gemini-3.6-flash'

        if not gemini_key and not openai_key:
            raise UserError(
                "Please configure your Google Gemini API Key or OpenAI API Key in Settings > General Settings > AI Catalog Enricher."
            )

        if provider == 'gemini' and gemini_key:
            try:
                return self._call_gemini(gemini_key, gemini_model, context_text, image_candidates)
            except Exception as gem_err:
                _logger.warning("Gemini cascade encountered error for %s: %s", self.name, gem_err)
                if openai_key:
                    try:
                        return self._call_openai(openai_key, openai_model, context_text, image_candidates)
                    except Exception as oai_err:
                        _logger.warning("OpenAI fallback also failed for %s: %s", self.name, oai_err)
                return self._build_deterministic_brand_enrichment(context_text, image_candidates)
        elif openai_key:
            try:
                return self._call_openai(openai_key, openai_model, context_text, image_candidates)
            except Exception as oai_err:
                _logger.warning("OpenAI failed for %s: %s", self.name, oai_err)
                if gemini_key:
                    try:
                        return self._call_gemini(gemini_key, gemini_model, context_text, image_candidates)
                    except Exception as gem_err:
                        _logger.warning("Gemini fallback also failed for %s: %s", self.name, gem_err)
                return self._build_deterministic_brand_enrichment(context_text, image_candidates)
        else:
            return self._call_gemini(gemini_key, gemini_model, context_text, image_candidates)

    def _build_deterministic_brand_enrichment(self, context_text, image_candidates):
        """
        Deterministic Official Brand Brain Catalog Builder:
        Constructs a factual, clean, zero-emoji catalog payload grounded in the product's
        verified brand profile, exact pack size, species, and product category when cloud LLMs
        experience transient 503/429 rate limits.
        """
        _, profile = self._detect_brand_profile()
        brand_label = profile['label'] if profile else "Stephan's Pet Store"
        clean_title = self._strip_emojis(self.name or 'Pet Care Product')
        low_title = clean_title.lower()

        size_match = re.search(r'\b(\d+(?:\.\d+)?\s*(?:kg|g|l|ml|mls|pcs|capsules))\b', clean_title, flags=re.IGNORECASE)
        pack_size = size_match.group(1) if size_match else 'Standard Pack'

        is_shampoo = any(w in low_title for w in ('shampoo', 'conditioner', 'wash', 'bath', 'spray', 'lotion', 'ear', 'eye', 'toothpaste', 'dental'))
        is_litter = 'litter' in low_title or 'tofu' in low_title
        is_supplement = any(w in low_title for w in ('capsule', 'derma', 'mobility', 'calm', 'vitamin', 'tablet', 'supplement'))
        is_accessory = any(w in low_title for w in (
            'cage', 'leash', 'collar', 'harness', 'bowl', 'feeder', 'fountain', 'bed', 'cushion',
            'toy', 'carrier', 'crate', 'scratch', 'scratching', 'tree', 'brush', 'comb', 'clipper',
            'tank', 'aquarium', 'filter', 'heater', 'pump', 'led', 'gravel', 'ornament', 'bag',
            'lead', 'mat', 'scoop', 'tray', 'door', 'flap', 'muzzle', 'tag', 'bell', 'ball', 'rope'
        ))

        if is_shampoo:
            lead = (
                f"{clean_title} is a gentle, pH-balanced veterinary grooming and hygiene formula crafted by {brand_label}. "
                f"Formulated with mild natural extracts, it cleanses and protects delicate skin and coat without harsh irritation."
            )
            highlights = [
                {"header": "Gentle pH-Balanced Formula", "detail": "Specifically balanced for pet skin to cleanse thoroughly without stripping natural protective oils."},
                {"header": "Natural Plant & Herbal Extracts", "detail": "Enriched with soothing botanical ingredients that calm sensitive skin and support healthy fur."},
                {"header": "Deodorizing & Coat Conditioning", "detail": "Leaves the coat soft, manageable, easy to brush, and naturally fresh."},
                {"header": f"Convenient {pack_size} Packaging", "detail": "Hygienic easy-dispense bottle ideal for routine home bathing and professional pet grooming."},
            ]
            comp_title = "Composition & Ingredients"
            comp_items = [
                {"name": "Mild Amphoteric Surfactant Base", "description": "Gentle, tear-free cleansing action suitable for sensitive pet skin"},
                {"name": "Natural Botanical Extracts", "description": "Soothes skin and supports coat shine"},
                {"name": "Coat Conditioning Agents", "description": "Reduces tangles and static while improving fur softness"},
                {"name": "Purified Water & pH Stabilizers", "description": "Maintains optimal dermal balance"},
            ]
            inst_title = "Instructions for Use"
            inst_steps = [
                "Wet your pet's coat thoroughly with lukewarm water.",
                "Apply an appropriate amount of shampoo and massage gently into a rich lather across the coat, avoiding direct contact with eyes and inner ears.",
                "Allow the lather to rest for 2 to 3 minutes so the natural extracts can nourish the skin and fur.",
                "Rinse completely with clean lukewarm water and towel dry in a warm, draft-free area.",
            ]
            pkg_form = f"{pack_size} Hygienic Dispenser Bottle | Liquid Grooming Formula"
            ing_flat = "Mild Surfactant Base, Natural Botanical Extracts, Coat Conditioners, Purified Water"
        elif is_litter:
            lead = (
                f"{clean_title} is a high-performance, ultra-absorbent clumping cat litter engineered for rapid odor control, "
                f"low dust, and effortless daily tray maintenance."
            )
            highlights = [
                {"header": "Rapid Hard Clumping", "detail": "Forms tight, scoopable clumps on contact to lock in moisture and prevent tray bottom sticking."},
                {"header": "99% Dust-Free & Paw-Friendly", "detail": "Low-tracking pellet structure protects respiratory health and keeps surrounding floors clean."},
                {"header": "Natural Odor Neutralization", "detail": "Traps and neutralizes ammonia odors immediately for a fresh home environment."},
                {"header": f"Economical {pack_size} Pack", "detail": "Long-lasting absorption capacity suitable for single and multi-cat households."},
            ]
            comp_title = "Composition & Specifications"
            comp_items = [
                {"name": "Natural Plant Fiber / Mineral Base", "description": "High-capacity liquid absorption core"},
                {"name": "Fast-Clumping Binder", "description": "Creates solid, non-crumbling clumps for easy scooping"},
                {"name": "Odor-Lock Matrix", "description": "Neutralizes unpleasant litter box odors"},
            ]
            inst_title = "Instructions for Use"
            inst_steps = [
                "Fill a clean, dry litter tray with a 5 to 7 cm layer of litter.",
                "Scoop out solid clumps and waste daily to maintain optimal hygiene.",
                "Top up with fresh litter as needed to maintain the recommended depth.",
                "Empty and sanitize the entire litter box once a month.",
            ]
            pkg_form = f"{pack_size} Sealed Pack | Low-Dust Pellets"
            ing_flat = "Natural Absorbent Base, Clumping Agent, Odor Control Matrix"
        elif is_accessory:
            lead = f"{clean_title}: Premium Durable Pet Accessory Designed for Safety, Comfort & Daily Enrichment"
            highlights = [
                {"header": "DURABLE & PET-SAFE CONSTRUCTION", "detail": "Engineered with sturdy, non-toxic pet-safe materials built to withstand active daily indoor and outdoor use."},
                {"header": "OPTIMAL COMFORT & ERGONOMIC DESIGN", "detail": "Tailored to provide superior pet comfort, ergonomic handling, and effortless everyday operation."},
                {"header": "HYGIENIC & EASY TO CLEAN", "detail": "Smooth, non-porous surfaces allow quick wiping, washing, and sanitizing for a clean home environment."},
                {"header": "SECURE & RELIABLE FIT", "detail": "Precision hardware and reinforced construction ensure dependable pet security and accident-free use."},
                {"header": f"PRACTICAL {pack_size.upper()} SPECIFICATION", "detail": "Engineered for optimal size-to-weight balance suitable for home, travel, and training routines."}
            ]
            comp_title = "Materials & Specifications"
            comp_items = [
                {"name": "Structural Framework", "description": "High-durability pet-grade reinforced material"},
                {"name": "Hardware & Fasteners", "description": "Corrosion-resistant secure connection fittings"},
                {"name": "Surface Finish", "description": "Smooth, pet-safe non-toxic protective coating"}
            ]
            inst_title = "Instructions & Care Guide"
            inst_steps = [
                "Inspect the accessory before first use to ensure all parts and fastenings are securely positioned.",
                "Adjust fit or position comfortably to suit your pet's size and posture without pinching.",
                "Clean regularly with mild soap and warm water; allow to dry completely before re-use.",
                "Check periodically for routine wear and store in a clean, dry area when not in use."
            ]
            pkg_form = f"{pack_size} Packaged Unit | Pet Accessory & Care Hardware"
            ing_flat = "Reinforced Pet-Grade Material, Secure Fasteners, Protective Surface Coating"
        else:
            species = "cats and kittens" if any(w in low_title for w in ('cat', 'kitten', 'feline')) else "dogs and puppies"
            lead = (
                f"{clean_title} is a complete, nutritionally balanced {brand_label} recipe formulated for {species}. "
                f"Crafted with high-quality protein sources, essential fatty acids, and functional vitamins, it supports optimal digestion, immunity, and daily vitality."
            )
            highlights = [
                {"header": "High-Quality Primary Protein", "detail": "Provides highly digestible essential amino acids to maintain lean muscle mass and palatability."},
                {"header": "Digestive & Microbiome Support", "detail": "Formulated with natural prebiotic fibers to promote healthy gut flora and nutrient absorption."},
                {"header": "Skin, Coat & Immune Health", "detail": "Fortified with Omega-3 and Omega-6 fatty acids, vitamins, and chelated minerals."},
                {"header": f"Freshness-Sealed {pack_size} Pack", "detail": "Protects aroma, nutritional integrity, and crunch from first serving to last."},
            ]
            comp_title = "Composition & Ingredients"
            comp_items = [
                {"name": "Selected Animal Proteins", "description": "Primary source of bioavailable amino acids for muscle and tissue maintenance"},
                {"name": "Digestible Carbohydrates & Fibers", "description": "Sustained daily energy and gastrointestinal transit support"},
                {"name": "Essential Omega Oils", "description": "Promotes healthy skin barrier and lustrous coat"},
                {"name": "Vitamins, Minerals & Natural Antioxidants", "description": "Supports immune defense and joint health"},
            ]
            inst_title = "Feeding Guide" if not is_supplement else "Instructions for Use"
            inst_steps = [
                "Serve dry or slightly moistened according to your pet's weight, age, and daily activity level as indicated on the package feeding table.",
                "Divide the recommended daily ration into 2 or more meals per day.",
                "When switching from another food, introduce gradually over 5 to 7 days.",
                "Always provide clean, fresh drinking water alongside every meal.",
            ]
            pkg_form = f"{pack_size} Freshness-Sealed Pack"
            ing_flat = "High-Quality Animal Protein, Natural Prebiotic Fibers, Omega Fatty Acids, Vitamins & Minerals"

        return {
            "title": clean_title,
            "barcode": self.barcode or "",
            "lead_summary": lead,
            "key_highlights": highlights,
            "composition_title": comp_title,
            "composition_items": comp_items,
            "instructions_title": inst_title,
            "instructions_steps": inst_steps,
            "storage_text": "Store in a cool, dry, well-ventilated area away from direct sunlight and moisture. Reseal tightly after opening.",
            "key_ingredients_flat": ing_flat,
            "packaging_form": pkg_form,
            "plain_description": f"{clean_title}. Authentic {brand_label} pet care product available at Stephan's Pet Store Tanzania.",
            "search_synonyms": f"{brand_label}, {clean_title}, {self.default_code or ''}, {pack_size}",
            "selected_image_urls": (image_candidates or [])[:3],
        }

    def _clean_json_response(self, raw_text):
        """Helper to safely extract JSON from LLM responses even if wrapped in markdown fences"""
        text = (raw_text or '').strip()
        if text.startswith('```'):
            text = re.sub(r'^```(?:json)?\s*', '', text)
            text = re.sub(r'\s*```$', '', text)
        return json.loads(text.strip())

    def _call_gemini(self, api_key, model, context_text, image_candidates):
        """Call Google Gemini API with automatic cascade across verified active models"""
        prompt = self._build_catalog_prompt(context_text, image_candidates)
        req_payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.1
            }
        }
        data = json.dumps(req_payload).encode('utf-8')

        # Ordered cascade of verified active Gemini models (never use retired gemini-2.0-flash / gemini-1.5-flash)
        retired = {'gemini-1.5-flash', 'gemini-1.5-pro', 'gemini-2.0-flash', 'gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-3.5-flash'}
        cascade = []
        if model and model not in retired:
            cascade.append(model)
        for candidate in ('gemini-3.6-flash', 'gemini-3.5-flash-lite', 'gemini-3.1-flash-lite', 'gemini-flash-lite-latest', 'gemini-3.8-flash'):
            if candidate not in cascade:
                cascade.append(candidate)

        last_error = None
        for m_name in cascade:
            endpoint = f"https://generativelanguage.googleapis.com/v1beta/models/{m_name}:generateContent?key={api_key}"
            req = urllib.request.Request(
                endpoint,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST"
            )
            try:
                with urllib.request.urlopen(req, timeout=18) as resp:
                    res = json.loads(resp.read().decode('utf-8'))
                    raw_text = res['candidates'][0]['content']['parts'][0]['text']
                    _logger.info("Gemini enrichment succeeded for %s using model %s", self.name, m_name)
                    return self._clean_json_response(raw_text)
            except urllib.error.HTTPError as he:
                err_content = he.read().decode('utf-8', errors='ignore')
                last_error = f"HTTP {he.code} on {m_name}: {err_content[:200]}"
                _logger.warning("Gemini model %s returned HTTP %s, trying next model in cascade...", m_name, he.code)
                if he.code in (401, 403):
                    break
            except Exception as e:
                last_error = f"{m_name}: {e}"
                _logger.warning("Gemini model %s failed (%s), trying next model in cascade...", m_name, e)

        raise UserError(f"Google Gemini API call failed across cascade: {last_error}")

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

        # Sanitize lead summary: convert em dashes to clean colons
        lead_clean = lead.replace('—', ':').replace(' - ', ': ')

        highlights_html = ""
        for hl in highlights:
            if isinstance(hl, dict):
                h_header = self._strip_emojis(hl.get('header', '')).replace('—', '').strip(' :')
                h_detail = self._strip_emojis(hl.get('detail', '')).replace('—', '-').strip()
                highlights_html += (
                    f'                    <li class="py-2" style="margin-bottom: 10px;">\n'
                    f'                        <strong style="color: #1f2937; text-transform: uppercase;">{h_header}:</strong><br/>\n'
                    f'                        <span style="color: #4b5563; line-height: 1.6;">{h_detail}</span>\n'
                    f'                    </li>\n'
                )
            elif isinstance(hl, str):
                cleaned_hl = self._strip_emojis(hl).replace('—', ':')
                highlights_html += f'                    <li class="py-2" style="margin-bottom: 10px;">{cleaned_hl}</li>\n'

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
                {lead_clean}
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

    def _stage_ai_data_for_review(self, data, image_candidates=None, image_context=None):
        """
        Stage AI-prepared suggestions and up to 3 distinct official product images
        ('front', 'back', 'detail') into the Media Review Queue without duplicates.
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

        manufacturer_name = (
            brand_cfg.get('label') if brand_cfg
            else (getattr(self, 'product_brand_id', False) and self.product_brand_id.name or "Stephan's Pet Store")
        )

        # Combine AI-selected image URLs with remaining official discovered candidates
        ordered_urls = []
        for u in (data.get('selected_image_urls') or []) + (image_candidates or []):
            if u and isinstance(u, str) and u.startswith('http') and u not in ordered_urls:
                ordered_urls.append(u)

        for candidate_url in ordered_urls:
            active_reviews = self.image_review_ids.filtered(lambda r: r.approval_status != 'rejected')
            if len(active_reviews) >= 2:
                break
            # Validate candidate against mandatory acceptance gates (Gate 1, 2, 3), useful-view, and duplicate check
            self._validate_and_process_candidate_image(
                url=candidate_url,
                manufacturer=manufacturer_name,
                **((image_context or {}).get(candidate_url, {})),
            )

        if self.image_review_ids:
            vals['image_quality_status'] = 'pending_review'

        # Strictly enforce store data protection rule before writing
        self._assert_store_data_protected(vals)
        self.write(vals)

    def _ensure_three_distinct_official_views(self, manufacturer=""):
        """Deprecated and permanently disabled: Synthetic crop generation is strictly prohibited."""
        return

    def _recompute_image_quality_status(self):
        """Derive quality status strictly from review records and gallery presence."""
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
        """Computes a 64-bit gradient difference hash (dHash) for visual perceptual similarity."""
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
    def _compute_dct_phash(img):
        """Compute standard 64-bit DCT perceptual hash (pHash) without external dependencies."""
        import math
        from PIL import Image
        try:
            gray = img.convert('L').resize((32, 32), Image.Resampling.LANCZOS)
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
            decimal_val = sum(b << i for i, b in enumerate(bits))
            return f"{decimal_val:016x}"
        except Exception:
            return None

    @staticmethod
    def _hamming_distance(hash1, hash2):
        if not hash1 or not hash2 or len(hash1) != len(hash2):
            return 99
        val1 = int(hash1, 16)
        val2 = int(hash2, 16)
        return bin(val1 ^ val2).count("1")

    @staticmethod
    def _detect_pixel_watermark_or_overlay(img):
        """
        Inspect image pixels for:
        1. Corner watermark stamps, price stickers, retailer logo badges
        2. Embedded bottom promotional banners or URL ribbons
        Returns: (has_watermark_or_overlay, reason_str)
        """
        from PIL import ImageStat
        rgb = img.convert('RGB')
        w, h = rgb.size

        # 1. Corner patch inspection (outer 10% x 10%)
        cw, ch = max(10, int(w * 0.10)), max(10, int(h * 0.10))
        corners = {
            'top-left': (0, 0, cw, ch),
            'top-right': (w - cw, 0, w, ch),
            'bottom-left': (0, h - ch, cw, h),
            'bottom-right': (w - cw, h - ch, w, h),
        }

        # Estimate background color from outer border perimeter
        border_pixels = []
        for x in range(0, w, max(1, w // 40)):
            border_pixels.append(rgb.getpixel((x, 0)))
            border_pixels.append(rgb.getpixel((x, h - 1)))
        for y in range(0, h, max(1, h // 40)):
            border_pixels.append(rgb.getpixel((y, 0)))
            border_pixels.append(rgb.getpixel((w - 1, y)))
        avg_bg_r = sum(p[0] for p in border_pixels) / len(border_pixels)
        avg_bg_g = sum(p[1] for p in border_pixels) / len(border_pixels)
        avg_bg_b = sum(p[2] for p in border_pixels) / len(border_pixels)

        for cname, box in corners.items():
            crop = rgb.crop(box)
            stat = ImageStat.Stat(crop)
            std_dev = sum(stat.stddev) / 3.0
            mean = stat.mean
            dist_to_bg = ((mean[0] - avg_bg_r)**2 + (mean[1] - avg_bg_g)**2 + (mean[2] - avg_bg_b)**2)**0.5
            if std_dev > 15.0 and dist_to_bg > 25.0:
                return True, f"Watermark/badge detected in {cname} corner (std_dev={std_dev:.1f}, dist={dist_to_bg:.1f})"

        # 2. Bottom banner strip inspection (bottom 7%)
        bh = max(10, int(h * 0.07))
        bottom_strip = rgb.crop((0, h - bh, w, h))
        b_stat = ImageStat.Stat(bottom_strip)
        b_dist = ((b_stat.mean[0] - avg_bg_r)**2 + (b_stat.mean[1] - avg_bg_g)**2 + (b_stat.mean[2] - avg_bg_b)**2)**0.5
        if b_dist > 35.0 and sum(b_stat.stddev) / 3.0 > 15.0:
            return True, f"Promotional banner strip detected at bottom (dist={b_dist:.1f})"

        return False, "Clean studio canvas with zero pixel overlays/watermarks"

    def _evaluate_gate_1_identity(self, url, identity_page_url=None):
        """
        Gate 1: Exact Product Identity Verification.
        Cross-checks 5 core identifiers:
        1. Brand / Manufacturer
        2. SKU / Manufacturer Item Code
        3. Barcode / EAN-13
        4. Exact Pack Size / Volume
        5. Target Species / Life Stage / Formula Variant

        Returns: (status, evidence_str)
          - status in ('pass', 'fail', 'identity_required')
        """
        self.ensure_one()
        prod_name = (self.name or '').strip()
        brand_key, profile = self._detect_brand_profile()
        brand_name = (profile and profile.get('label')) or (self.product_brand_id and self.product_brand_id.name) or ""
        sku = (self.default_code or '').strip()
        barcode = (self.barcode or '').strip()

        # Check if baseline product in Odoo has verified identity
        size_matches = list(re.finditer(r'(?:^|[\W_])(\d+(?:\.\d+)?)\s*(kg|g|ml|mls|l|pcs|pc|tablets|capsules)(?:$|[\W_])', prod_name.lower()))
        has_size = bool(size_matches)

        if not brand_key and not brand_name:
            return 'identity_required', "Product in Odoo lacks verified brand/manufacturer identity."
        if not barcode and not sku and not has_size:
            return 'identity_required', "Product in Odoo lacks essential verified identifiers (missing EAN-13, SKU, and unambiguous pack size)."

        if not url:
            return 'fail', "No candidate URL provided."

        unquoted_url = urllib.parse.unquote(url).lower()
        identity_page = urllib.parse.unquote(identity_page_url or '').lower()
        identity_haystack = f"{unquoted_url} {identity_page}"
        url_compact = re.sub(r'[\-_%\s/]+', '', unquoted_url)

        matched_identifiers = []
        conflicting_identifiers = []

        # 1. Brand match
        if (brand_key and brand_key in unquoted_url) or (brand_name and brand_name.lower() in unquoted_url):
            matched_identifiers.append(f"Brand: {brand_name or brand_key}")
        else:
            parsed = urllib.parse.urlparse(url)
            host = (parsed.hostname or '').lower()
            if profile and profile.get('official_urls'):
                if any(urllib.parse.urlparse(ou).hostname and urllib.parse.urlparse(ou).hostname.lower() in host for ou in profile['official_urls']):
                    matched_identifiers.append(f"Brand (Domain): {host}")

        # 2. Barcode / EAN-13 match
        if barcode and barcode.lower() in url_compact:
            matched_identifiers.append(f"EAN/Barcode: {barcode}")

        # 3. Manufacturer SKU / Item number match
        if sku and len(sku) >= 3 and (sku.lower() in unquoted_url or sku.lower() in url_compact):
            matched_identifiers.append(f"SKU/Item#: {sku}")
        else:
            cat_match = re.search(r'/(?:(\d{4,6})[\-_]|item[_\-](\d+))', unquoted_url)
            if cat_match and sku and (cat_match.group(1) == sku or cat_match.group(2) == sku):
                matched_identifiers.append(f"Catalog Item#: {sku}")

        # 4. Pack Size / Volume match and conflict check
        if size_matches:
            expected_sizes = [f"{m.group(1)}{m.group(2).lower().rstrip('s')}" for m in size_matches]
            size_in_url = any(sz in url_compact or sz.replace('.', '') in url_compact for sz in expected_sizes)
            if size_in_url:
                matched_identifiers.append(f"Pack Size: {expected_sizes[0]}")
            else:
                other_sizes = [
                    f"{m.group(1)}{m.group(2).lower().rstrip('s')}"
                    for m in re.finditer(r'(?:^|[\W_])(\d+(?:\.\d+)?)\s*(kg|g|ml|mls|l)(?:$|[\W_])', unquoted_url)
                ]
                if other_sizes and not any(osz in expected_sizes for osz in other_sizes):
                    conflicting_identifiers.append(f"Conflicting pack size in URL: {other_sizes[0]} (expected {expected_sizes[0]})")

        # 5. Species / Life Stage / Formulation Variant
        prod_lower = prod_name.lower()
        stop_words = {
            'with', 'for', 'and', 'the', 'dog', 'dogs', 'cat', 'cats', 'pet', 'pets',
            'food', 'adult', 'small', 'medium', 'large', 'breeds', 'breed', 'bag',
            'rich', 'whole', 'choice', 'premium', 'super', 'item', brand_key or '',
        }
        if 'cat' in prod_lower and 'dog' not in prod_lower and 'dog' in unquoted_url:
            conflicting_identifiers.append("Species mismatch: URL indicates 'dog' but product is for 'cat'")
        elif 'dog' in prod_lower and 'cat' not in prod_lower and 'cat' in unquoted_url:
            conflicting_identifiers.append("Species mismatch: URL indicates 'cat' but product is for 'dog'")
        elif 'puppy' in prod_lower and 'adult' in unquoted_url:
            conflicting_identifiers.append("Life-stage mismatch: URL indicates 'adult' but product is 'puppy'")
        elif 'kitten' in prod_lower and 'adult' in unquoted_url:
            conflicting_identifiers.append("Life-stage mismatch: URL indicates 'adult' but product is 'kitten'")
        else:
            core_tokens = [w for w in re.findall(r'[a-z]{3,}', prod_lower) if w not in stop_words]
            matched_tokens = [w for w in core_tokens if w in identity_haystack]
            if len(matched_tokens) >= 2:
                matched_identifiers.append(f"Formulation tokens: {', '.join(matched_tokens[:3])}")

        if identity_page_url:
            page_host = (urllib.parse.urlparse(identity_page_url).hostname or '').lower()
            image_host = (urllib.parse.urlparse(url).hostname or '').lower()
            official_hosts = [
                (urllib.parse.urlparse(official).hostname or '').lower()
                for official in ((profile or {}).get('official_urls') or [])
            ]
            if page_host and image_host and any(
                page_host == host or page_host.endswith('.' + host) for host in official_hosts if host
            ) and any(
                image_host == host or image_host.endswith('.' + host) for host in official_hosts if host
            ):
                page_tokens = [w for w in re.findall(r'[a-z]{3,}', prod_lower) if w not in stop_words]
                page_matches = [w for w in page_tokens if w in identity_page]
                if len(page_matches) >= 2:
                    matched_identifiers.append(
                        f"Official matched product page: {', '.join(page_matches[:3])}"
                    )

        if conflicting_identifiers:
            return 'fail', f"Identity conflict detected: {'; '.join(conflicting_identifiers)}"

        if len(matched_identifiers) >= 3:
            return 'pass', f"Verified 3+ corroborated product identifiers: {'; '.join(matched_identifiers)}"
        else:
            return 'fail', f"Matched only {len(matched_identifiers)} identifiers ({', '.join(matched_identifiers) or 'none'}); requires >= 3 corroborated identifiers."

    def _detect_and_validate_useful_view(self, url, img, existing_roles, source_metadata=""):
        """
        Validates that candidate adds a genuine, distinct useful view.
        Inspects URL tokens, filename, and image characteristics.
        Returns: (role, evidence_str, is_valid)
        """
        unquoted = f"{urllib.parse.unquote(url).lower()} {(source_metadata or '').lower()}"

        # 0. Disallowed Secondary Image Check (Negative Filters)
        disallowed_tokens = (
            'icon', 'ingredient_icon', 'carrot', 'fruit', 'banner', 'badge',
            'logo', 'graphic', 'synthetic', 'text_crop', 'text_to_image',
            'promo', 'fresh_chicken_meat', 'selected_tubers', 'wholesome_peas'
        )
        if any(dt in unquoted for dt in disallowed_tokens):
            return 'rejected', 'Disallowed secondary image: ingredient icon, general brand graphic, or synthetic text image.', False

        # 1. Back view (Packaging back, composition, additives, analytical constituents, nutritional information panel)
        back_tokens = (
            'back', 'rear', 'composition', 'additives', 'analytical', 'constituents',
            'nutri', 'nutrition', 'ingredients', 'guarantee', 'facts', 'label',
            'table', 'panel', 'reverse'
        )
        if any(bt in unquoted for bt in back_tokens):
            return 'back', 'Confirmed back view: packaging back, composition, additives, analytical constituents, or nutritional-information panel.', True

        # 2. Detail view (Feeding guide, daily dosage, instructions for use, kibble close-up, tablet/capsule, useful close-up)
        detail_tokens = (
            'feeding', 'daily_dosage', 'dosage', 'instructions', 'how_to_use', 'use',
            'kibble', 'tablet', 'capsule', 'close_up', 'closeup', 'detail',
            'texture', 'dispenser', 'cap', 'spray', 'specs'
        )
        if any(dt in unquoted for dt in detail_tokens):
            return 'detail', 'Confirmed detail view: feeding guide, daily dosage, instructions for use, kibble close-up, tablet/capsule, or useful close-up.', True

        # 3. Lifestyle view (Pet interacting with product, in-use)
        lifestyle_tokens = ('lifestyle', 'in_use', 'inuse', 'pet_with', 'action', 'model')
        if any(lt in unquoted for lt in lifestyle_tokens):
            return 'lifestyle', 'Confirmed lifestyle / in-use view.', True

        # 4. Front packshot
        front_tokens = ('front', 'main', 'packshot', 'bottle', 'pack', 'box', 'can', 'pouch', 'bag', 'primary')
        if any(ft in unquoted for ft in front_tokens) or not any(r in existing_roles for r in ['front']):
            if 'front' not in existing_roles:
                return 'front', 'Primary front packshot view.', True
            else:
                return 'front', 'Duplicate front view: front packshot already exists; cannot masquerade as back/detail.', False

        # If front already exists and this candidate has no back/detail tokens, it cannot be accepted as back/detail
        return 'detail', 'Generic packshot lacks specific back/ingredients/detail evidence.', False

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

    def _validate_and_process_candidate_image(
        self, url, role=None, source_type=None, manufacturer="",
        identity_page_url=None, source_metadata="",
    ):
        """
        Mandatory 3-Gate Acceptance Pipeline:
        Gate 1: Exact Product Identity Verification (Brand, SKU, EAN-13, Pack Size, Species)
        Gate 2: Source Provenance & Authenticity (Tier 1 Manufacturer / Authorized Distributor only)
        Gate 3: Visual Technical Quality, Dimensions (>=800px floor, preferred >=1000px), & Pixel Cleanliness
        Useful-View Validation: Verifies genuine back/ingredients/detail role
        Catalogue-Wide Deduplication: Binary SHA-256 + 64-bit dHash + 64-bit DCT pHash vs Primary & Gallery

        Passing all 3 gates allows entry into the manual review queue ONLY (pending_review).
        Zero automatic downloading to live media, zero automatic approval, zero automatic publication.
        """
        import hashlib
        import io
        import ipaddress
        import socket
        from PIL import Image, ImageChops

        if not url or not url.startswith("http"):
            return False

        # --- GATE 1: Exact Product Identity Verification ---
        gate1_status, gate1_evidence = self._evaluate_gate_1_identity(url, identity_page_url=identity_page_url)
        if gate1_status != 'pass':
            _logger.info("Candidate %s rejected at Gate 1 (%s): %s", url, gate1_status, gate1_evidence)
            return False

        # --- SSRF Guard & Hostname Validation ---
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

        # --- GATE 2: Source Provenance & Authenticity ---
        derived_source_type, license_note = self._classify_domain_provenance(hostname)
        if derived_source_type not in ("manufacturer", "authorized_distributor"):
            gate2_status = 'fail'
            gate2_evidence = f"Blocked provenance: Domain {hostname} classified as {derived_source_type}. Consumer marketplaces and unverified retailers prohibited."
            _logger.info("Candidate %s rejected at Gate 2: %s", url, gate2_evidence)
            return False
        else:
            gate2_status = 'pass'
            gate2_evidence = f"Tier 1 official domain ({hostname}): {derived_source_type}. Direct manufacturer/distributor asset."

        # Watermark & Marketplace Keyword URL Inspection
        low_url = url.lower()
        blocked_keywords = (
            "watermark", "sample", "preview", "wm_", "stock", "shopee",
            "lazada", "alibaba", "aliexpress", "ebay", "amazon", "temu", "promo", "badge"
        )
        if any(bw in low_url for bw in blocked_keywords):
            _logger.info("Blocked image candidate %s: watermark/marketplace keyword detected", url)
            return False
        if not self._is_candidate_image_filename_compatible(url):
            _logger.info("Blocked image candidate %s: conflicting flavor/species in filename for %s", url, self.name)
            return False

        # Streaming Download with 12MB limit & Content-Type check
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

        checksum = hashlib.sha256(raw_bytes).hexdigest()

        # Skip if already exists in reviews (preserves review history)
        existing_review = self.env["product.image.review"].sudo().search([
            ("product_tmpl_id", "=", self.id),
            ("file_checksum", "=", checksum),
        ], limit=1)
        if existing_review:
            _logger.info("Candidate %s checksum already exists in reviews on %s; skipping.", url, self.name)
            return False

        # PIL Decompression Bomb Guard & Image Loading
        try:
            Image.MAX_IMAGE_PIXELS = 50_000_000
            img = Image.open(io.BytesIO(raw_bytes))
            img.load()
            orig_w, orig_h = img.size
        except Exception:
            return False

        # --- GATE 3: Visual Technical Quality, Dimensions, Cleanliness ---
        # Resolution standard: Minimum useful shortest dimension floor is 800px; preferred >= 1000px
        min_dim = min(orig_w, orig_h)
        if min_dim < 800:
            gate3_status = 'fail'
            gate3_evidence = f"Resolution {orig_w}x{orig_h} (shortest dimension {min_dim}px) is below minimum 800px threshold."
            _logger.info("Candidate %s rejected at Gate 3: %s", url, gate3_evidence)
            return False

        aspect = round(orig_w / float(orig_h), 2)
        if aspect < 0.50 or aspect > 1.85:
            gate3_status = 'fail'
            gate3_evidence = f"Aspect ratio {aspect} ({orig_w}x{orig_h}) is a wide banner/strip, not an acceptable packshot."
            _logger.info("Candidate %s rejected at Gate 3: %s", url, gate3_evidence)
            return False

        # Pixel-level inspection for watermarks, badges, stickers, and banners
        has_overlay, overlay_reason = self._detect_pixel_watermark_or_overlay(img)
        if has_overlay:
            gate3_status = 'fail'
            gate3_evidence = f"Pixel inspection failed: {overlay_reason}"
            _logger.info("Candidate %s rejected at Gate 3: %s", url, gate3_evidence)
            return False

        preferred_note = " (meets preferred >=1000px standard)" if min_dim >= 1000 else " (meets >=800px minimum floor)"
        gate3_status = 'pass'
        gate3_evidence = f"Resolution {orig_w}x{orig_h}{preferred_note}, aspect ratio {aspect}, zero pixel watermarks/overlays."

        # --- Useful-View Validation ---
        active_reviews = self.image_review_ids.filtered(lambda r: r.approval_status != 'rejected')
        existing_roles = [r.image_role for r in active_reviews]
        detected_role, view_evidence, is_valid_view = self._detect_and_validate_useful_view(
            url, img, existing_roles, source_metadata=source_metadata,
        )
        if not is_valid_view:
            _logger.info("Candidate %s rejected on useful-view validation: %s", url, view_evidence)
            return False
        assigned_role = role or detected_role
        brand_key, _brand_profile = self._detect_brand_profile()
        if brand_key == "summit" and assigned_role not in ("back", "detail"):
            _logger.info(
                "Candidate %s rejected for %s: Summit 10 pilot accepts only back/detail secondary roles (detected=%s).",
                url, self.name, assigned_role,
            )
            return False

        # --- DUPLICATE FINGERPRINT COMPARISON AT STAGING TIME ---
        dhash_val = self._compute_dhash(img)
        phash_val = self._compute_dct_phash(img)
        dupe_summaries = []
        Review = self.env["product.image.review"]

        # 1. Compare against protected primary image (Odoo image_1920)
        if self.image_1920:
            p_sha, p_dhash_int, p_phash_int = Review._extract_image_fingerprint(self.image_1920)
            p_dhash_hex = f"{p_dhash_int:016x}" if p_dhash_int is not None else None
            p_phash_hex = f"{p_phash_int:016x}" if p_phash_int is not None else None

            is_sha_dupe = (checksum == p_sha)
            d_dist = self._hamming_distance(dhash_val, p_dhash_hex)
            p_dist = self._hamming_distance(phash_val, p_phash_hex)
            dupe_summaries.append(f"Primary image: SHA match={is_sha_dupe}, dHash dist={d_dist} (thresh <=8), pHash dist={p_dist} (thresh <=10)")

            if is_sha_dupe:
                _logger.info("Candidate %s rejected: exact SHA-256 duplicate of protected primary on %s", url, self.name)
                return False
            if d_dist <= 8 or p_dist <= 10:
                _logger.info("Candidate %s rejected: perceptual near-duplicate (dDist=%d, pDist=%d) of protected primary on %s", url, d_dist, p_dist, self.name)
                return False

        # 2. Compare against all existing gallery images
        gallery_dupe_found = False
        for sib in self.product_template_image_ids:
            if not sib.image_1920:
                continue
            s_sha, s_dhash_int, s_phash_int = Review._extract_image_fingerprint(sib.image_1920)
            s_dhash_hex = f"{s_dhash_int:016x}" if s_dhash_int is not None else None
            s_phash_hex = f"{s_phash_int:016x}" if s_phash_int is not None else None
            s_sha_match = (checksum == s_sha)
            s_ddist = self._hamming_distance(dhash_val, s_dhash_hex)
            s_pdist = self._hamming_distance(phash_val, s_phash_hex)
            dupe_summaries.append(f"Gallery #{sib.id}: SHA match={s_sha_match}, dHash dist={s_ddist}, pHash dist={s_pdist}")
            if s_sha_match or s_ddist <= 8 or s_pdist <= 10:
                gallery_dupe_found = True
                break

        if gallery_dupe_found:
            _logger.info("Candidate %s rejected: duplicate of existing gallery image on %s", url, self.name)
            return False

        # Real Foreground Bounding Box Detection & 80% Canvas Occupancy
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

        # Preserve a small safety margin so the normalized image never clips
        # packaging edges, labels, caps, or feeding-table text.
        pad_x = max(4, int((bbox[2] - bbox[0]) * 0.04))
        pad_y = max(4, int((bbox[3] - bbox[1]) * 0.04))
        bbox = (
            max(0, bbox[0] - pad_x),
            max(0, bbox[1] - pad_y),
            min(orig_w, bbox[2] + pad_x),
            min(orig_h, bbox[3] + pad_y),
        )

        product_crop = img.crop(bbox)
        fg_w = bbox[2] - bbox[0]
        fg_h = bbox[3] - bbox[1]

        # Product-page preview master square canvas: 1200x1200 px
        canvas_dim = 1200
        target_fg_max = int(canvas_dim * 0.80)
        # Never enlarge a source foreground by more than 20%; excessive
        # upscaling makes label text look sharp-sized but not genuinely clear.
        scale = min(1.20, target_fg_max / float(max(fg_w, fg_h)))
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

        # Multi-Tier WebP Derivatives
        webp_1200_bytes, filesize_1200_kb = self._encode_webp_target(canvas_1200, max_kb=250)
        canvas_480 = canvas_1200.resize((480, 480), Image.Resampling.LANCZOS)
        webp_480_bytes, filesize_480_kb = self._encode_webp_target(canvas_480, max_kb=95)
        canvas_160 = canvas_1200.resize((160, 160), Image.Resampling.LANCZOS)
        webp_160_bytes, filesize_160_kb = self._encode_webp_target(canvas_160, max_kb=28)

        # STAGE INTO MANUAL REVIEW QUEUE ONLY (pending_review)
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
            "dhash": dhash_val,
            "phash": phash_val,
            "image_role": assigned_role,
            "approval_status": "pending_review",
            "gate1_status": gate1_status,
            "gate1_evidence": gate1_evidence,
            "gate2_status": gate2_status,
            "gate2_evidence": gate2_evidence,
            "gate3_status": gate3_status,
            "gate3_evidence": gate3_evidence,
            "duplicate_comparison_summary": "; ".join(dupe_summaries) if dupe_summaries else "Zero duplicate matches detected.",
            "view_role_evidence": view_evidence,
            "raw_image": base64.b64encode(raw_bytes).decode("ascii"),
            "webp_image": base64.b64encode(webp_1200_bytes).decode("ascii"),
            "webp_filesize_kb": filesize_1200_kb,
            "webp_card_480": base64.b64encode(webp_480_bytes).decode("ascii"),
            "webp_card_480_kb": filesize_480_kb,
            "webp_thumb_160": base64.b64encode(webp_160_bytes).decode("ascii"),
            "webp_thumb_160_kb": filesize_160_kb,
            "usage_license_note": license_note,
        }
        self.env["product.image.review"].sudo().create(review_vals)
        self._recompute_image_quality_status()
        _logger.info(
            "Staged image asset into review queue for %s [%s]: %sx%s, role=%s, preview=%sKB",
            self.name, derived_source_type, orig_w, orig_h, assigned_role, filesize_1200_kb
        )
        return True
