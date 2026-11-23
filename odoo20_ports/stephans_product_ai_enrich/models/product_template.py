import base64
import json
import logging
import re
import urllib.request
import urllib.parse
from bs4 import BeautifulSoup

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

DEFAULT_SEEDED_URLS = """https://www.biolinepet.com/
https://summit10.com/
https://tropicat.eu/
https://tropidog.eu/"""

DEFAULT_KEYWORDS = "premium pet care, safe natural ingredients, Dar es Salaam Tanzania, Stephan's Pet Store"

# ==============================================================================
# OFFICIAL BRAND CATALOG BRAIN
# Priority Tier 1: Stephan's 4 Active Flagship Brands (Processed FIRST)
# Priority Tier 2: Secondary Veterinary / Nutrition & Trusted Pet Catalogues
# ==============================================================================
FLAGSHIP_BRAND_KEYS = ('bioline', 'summit', 'tropicat', 'tropidog', 'tropifit', 'tropical')

OFFICIAL_BRAND_CATALOG_BRAIN = {
    # --- TIER 1: 4 ACTIVE FLAGSHIP BRANDS ---
    'bioline': {
        'label': 'Bioline',
        'tier': 1,
        'official_urls': [
            'https://www.biolinepet.com/',
            'https://vetforest.com/',
            'https://www.petzone.com/',
        ],
        'search_templates': [
            'https://www.biolinepet.com/?s={query}',
            'https://vetforest.com/search?q={query}',
        ],
        'keywords': 'Bioline pet care, gentle grooming, hygiene, safe formula, veterinary-grade, natural extracts',
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
            'https://summit10.com/',
        ],
        'search_templates': [
            'https://summit10.com/?s={query}',
        ],
        'keywords': 'Summit 10, super-premium nutrition, 10 natural ingredients, complete balanced pet food, Cotecnica Spain',
        'guidelines': (
            'Official Summit 10 (Cotecnica, Spain) pet nutrition. Extract real meat/protein sources, '
            'analytical constituents (crude protein, fat, fiber, ash), life-stage/breed size, and daily feeding guide.'
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
        'search_templates': [
            'https://tropicat.eu/?s={query}',
        ],
        'keywords': 'TropiCat, Tropical Poland, complete cat nutrition, taurine, healthy digestion, coat shine',
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
        'search_templates': [
            'https://tropidog.eu/?s={query}',
        ],
        'keywords': 'TropiDog, Tropical Poland, premium dog nutrition, omega fatty acids, dental & joint care',
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
        'search_templates': [
            'https://tropifit.eu/?s={query}',
        ],
        'keywords': 'Tropifit, Tropical Poland, small animal nutrition, rabbit, guinea pig, hamster, natural herbs & fiber',
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
        'search_templates': [
            'https://tropical.pl/en/?s={query}',
        ],
        'keywords': 'Tropical Poland, aquarium fish food, flakes, granules, balanced aquatic nutrition',
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
        'search_templates': [],
        'keywords': 'Bravecto, MSD Animal Health, fluralaner, 12-week flea and tick protection',
        'guidelines': 'Official MSD Animal Health Bravecto. Strictly preserve the exact pet weight band in the product name. Never invent dosages.',
        'is_vet_medicine': True,
    },
    'nexgard': {
        'label': 'NexGard',
        'tier': 2,
        'official_urls': ['https://www.nexgard.com/'],
        'search_templates': [],
        'keywords': 'NexGard Spectra, Boehringer Ingelheim, flea tick worm chewable',
        'guidelines': 'Official Boehringer Ingelheim NexGard. Strictly preserve the exact weight range in the title. Never invent dosages.',
        'is_vet_medicine': True,
    },
    'milbemax': {
        'label': 'Milbemax',
        'tier': 2,
        'official_urls': ['https://www.elanco.com/'],
        'search_templates': [],
        'keywords': 'Milbemax, Elanco, broad-spectrum dewormer tablets',
        'guidelines': 'Official Elanco Milbemax dewormer. Strictly preserve pet species and weight band. Never invent dosages.',
        'is_vet_medicine': True,
    },
    'f10': {
        'label': 'F10',
        'tier': 2,
        'official_urls': ['https://www.f10products.co.uk/'],
        'search_templates': [],
        'keywords': 'F10 Veterinary Products, germicidal, antiseptic wound care',
        'guidelines': 'Official F10 Veterinary Products. Include safe veterinary usage directions.',
        'is_vet_medicine': True,
    },
    'josera': {
        'label': 'Josera',
        'tier': 2,
        'official_urls': ['https://www.josera.com/'],
        'search_templates': ['https://www.josera.com/catalogsearch/result/?q={query}'],
        'keywords': 'Josera Germany, super-premium pet food, no artificial colors or preservatives',
        'guidelines': 'Official Josera (Germany) pet food. Highlight German quality, ingredients, and feeding guidelines.',
        'is_vet_medicine': False,
    },
    'whiskas': {
        'label': 'Whiskas',
        'tier': 2,
        'official_urls': ['https://www.whiskas.co.uk/'],
        'search_templates': [],
        'keywords': 'Whiskas, Mars Petcare, complete cat food, balanced nutrition',
        'guidelines': 'Official Whiskas cat food. Highlight flavor, life-stage nutrition, and feeding guide.',
        'is_vet_medicine': False,
    },
    'ownat': {
        'label': 'Ownat',
        'tier': 2,
        'official_urls': ['https://www.ownat.com/en/'],
        'search_templates': [],
        'keywords': 'Ownat, Cotecnica Spain, natural ingredients, fresh meat pet food',
        'guidelines': 'Official Ownat (Cotecnica, Spain) natural pet food. Highlight natural ingredients and feeding guide.',
        'is_vet_medicine': False,
    },
}

GENERAL_CATALOG_FALLBACK_URLS = [
    'https://www.petzone.com/',
    'https://www.zooplus.com/',
    'https://www.trixie.de/en/',
    'https://www.ferplast.com/',
]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

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
    x_key_ingredients = fields.Text(
        string="Key Ingredients / Composition",
        help="Extracted raw materials or ingredients (e.g. Bean Dregs, Bentonite Clay, Corn Starch, Guar Gum)."
    )
    x_packaging_form = fields.Char(
        string="Packaging & Form",
        help="Physical form and packaging (e.g. 6L / ~2.5 kg Vacuum-Sealed Pack, Cylindrical Pellets)."
    )
    x_ai_enriched = fields.Boolean(
        string="AI Enriched",
        default=False,
        index=True,
        help="Checked automatically once this product has been enriched by the AI Catalog Engine."
    )
    x_ai_last_enriched = fields.Datetime(
        string="Last AI Enrichment",
        readonly=True,
    )
    x_ai_last_error = fields.Text(
        string="Last AI Error",
        readonly=True,
    )

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

    def _build_official_seed_urls(self):
        """Build official brand product search + homepage URLs for this product."""
        self.ensure_one()
        _, profile = self._detect_brand_profile()
        clean_name = re.sub(r'\s+', ' ', (self.name or '').strip())
        # Keep first 5 meaningful words for clean search queries
        short_query = ' '.join(clean_name.split()[:5])
        encoded_q = urllib.parse.quote_plus(short_query)

        urls = []
        if profile:
            for tmpl in profile.get('search_templates', []):
                urls.append(tmpl.format(query=encoded_q))
            for u in profile.get('official_urls', []):
                if u not in urls:
                    urls.append(u)
        else:
            urls.extend(GENERAL_CATALOG_FALLBACK_URLS)
        return urls

    def action_seed_official_brand_urls(self):
        """Seed official manufacturer URLs & keywords into this product record."""
        for rec in self:
            _, profile = rec._detect_brand_profile()
            official_urls = rec._build_official_seed_urls()

            # Preserve any existing custom product-specific links (excluding generic defaults)
            existing = [
                u.strip() for u in (rec.x_source_urls or '').splitlines()
                if u.strip().startswith('http')
                and 'amazon.ae/Bioline-Tofu' not in u
                and 'katzeom.com/products/bioline-tofu' not in u
                and 'noon.com/uae-en/bioline-tofu' not in u
                and 'preview.stephanspetstore.co.tz' not in u
            ]
            # Put official brand URLs first, then any custom specific links
            merged = []
            for u in official_urls + existing:
                if u not in merged:
                    merged.append(u)

            vals = {'x_source_urls': '\n'.join(merged[:6])}
            if profile and (not rec.x_keywords or rec.x_keywords == DEFAULT_KEYWORDS or 'okara bean dregs' in (rec.x_keywords or '').lower()):
                if 'litter' not in (rec.name or '').lower():
                    vals['x_keywords'] = profile['keywords']
            rec.write(vals)
        return True

    def action_regenerate_ai_details(self):
        """Action triggered by the '⚡ Regenerate Details (AI)' button"""
        self.ensure_one()

        # 0. Ensure official brand URLs are seeded if missing or stale
        if not self.x_source_urls or 'amazon.ae/Bioline-Tofu' in (self.x_source_urls or ''):
            if 'litter' not in (self.name or '').lower():
                self.action_seed_official_brand_urls()

        # 1. Fetch & parse content from seeded and custom reference URLs
        scraped_text, image_candidates = self._fetch_catalog_sources()

        # 2. Query AI Engine (Gemini or OpenAI depending on Settings)
        ai_data = self._call_ai_engine(scraped_text, image_candidates)

        # 3. Apply structured outputs to product record
        self._apply_ai_data_to_product(ai_data)

        self.write({
            'x_ai_enriched': True,
            'x_ai_last_enriched': fields.Datetime.now(),
            'x_ai_last_error': False,
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'AI Catalog Regeneration Complete',
                'message': f"Product '{self.name}' has been successfully enriched with standardized catalog details, barcode, and media!",
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def cron_auto_enrich_products(self, limit=5):
        """
        Scheduled Action: Automatically enrich `limit` (default 5) products every 30 minutes.
        Priority Order:
          1. Stephan's 4 Active Flagship Brands (Bioline, Summit 10, TropiCat, TropiDog / Tropifit / Tropical)
          2. Remaining published, in-stock catalog products
        """
        ir_config = self.env['ir.config_parameter'].sudo()
        gemini_key = (ir_config.get_param('stephans_product_ai_enrich.gemini_api_key') or '').strip()
        openai_key = (ir_config.get_param('stephans_product_ai_enrich.openai_api_key') or '').strip()
        if not gemini_key and not openai_key:
            _logger.info(
                "AI Auto-Enrich Cron skipped: No Gemini or OpenAI API key configured in Settings > General Settings."
            )
            return

        base_domain = [
            ('active', '=', True),
            ('sale_ok', '=', True),
            ('x_ai_enriched', '=', False),
            ('x_ai_last_error', '=', False),
        ]

        # Tier 0: Start automatically from Summit brand FIRST
        batch = self.search(
            base_domain + [('name', 'ilike', 'summit')],
            order='is_published desc, list_price desc, id asc',
            limit=limit,
        )

        # Tier 1: Remaining flagship brands (Bioline, TropiCat, TropiDog, Tropifit, Tropical)
        if len(batch) < limit:
            remaining = limit - len(batch)
            other_flagships = tuple(bk for bk in FLAGSHIP_BRAND_KEYS if bk != 'summit')
            flagship_or = ['|'] * (len(other_flagships) - 1)
            for bk in other_flagships:
                flagship_or.append(('name', 'ilike', bk))

            extra_flagship = self.search(
                base_domain + [('id', 'not in', batch.ids)] + flagship_or,
                order='is_published desc, list_price desc, id asc',
                limit=remaining,
            )
            batch |= extra_flagship

        # Tier 2: Once all flagship brands are done, continue with the rest of the catalog
        if len(batch) < limit:
            remaining = limit - len(batch)
            extra = self.search(
                base_domain + [('id', 'not in', batch.ids)],
                order='is_published desc, list_price desc, id asc',
                limit=remaining,
            )
            batch |= extra

        if not batch:
            _logger.info("AI Auto-Enrich Cron: All active products are already enriched!")
            return

        _logger.info("AI Auto-Enrich Cron: Processing batch of %d products: %s", len(batch), batch.mapped('name'))
        for product in batch:
            try:
                product.action_seed_official_brand_urls()
                product.action_regenerate_ai_details()
                self.env.cr.commit()
                _logger.info("AI Auto-Enrich Cron: Successfully enriched [%s] %s", product.id, product.name)
            except Exception as e:
                self.env.cr.rollback()
                err_msg = str(e)[:500]
                _logger.warning("AI Auto-Enrich Cron: Failed on [%s] %s: %s", product.id, product.name, err_msg)
                # Do not permanently mark transient auth/quota errors so they retry once key is updated
                if not any(code in err_msg for code in ('401', '403', '429', 'configure your')):
                    product.write({'x_ai_last_error': err_msg})
                    self.env.cr.commit()
                else:
                    # Stop the rest of this batch on auth/quota errors
                    break

    def _fetch_catalog_sources(self):
        """Fetch raw HTML, text and high-res clean images from given URLs"""
        urls = [u.strip() for u in (self.x_source_urls or '').split('\n') if u.strip().startswith('http')]
        combined_text = (
            f"Current Product Name: {self.name}\n"
            f"Default SKU: {self.default_code or ''}\n"
            f"User Target Keywords: {self.x_keywords or ''}\n\n"
        )
        image_candidates = []
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        for url in urls:
            try:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    html = resp.read().decode('utf-8', errors='ignore')
                    soup = BeautifulSoup(html, 'html.parser')

                    # Remove unwanted tags
                    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'noscript', 'svg']):
                        tag.decompose()

                    text = soup.get_text(' ', strip=True)[:3500]
                    combined_text += f"\n--- Source URL: {url} ---\n{text}\n"

                    # Collect candidate product images
                    for img in soup.find_all('img'):
                        src = img.get('src') or img.get('data-src') or ''
                        if not src:
                            continue
                        if src.startswith('//'):
                            src = 'https:' + src

                        src_lower = src.lower()
                        # Skip logos, badges, payment icons, tracking pixels, watermarked banners
                        if any(b in src_lower for b in ['logo', 'icon', 'badge', 'payment', 'watermark', 'banner', 'thumb']):
                            continue

                        # Upgrade Shopify/CDN image dimensions to maximum clean resolution
                        full_res_src = re.sub(r'_\d+x\d*\.', '.', src)
                        full_res_src = re.sub(r'width=\d+', 'width=1920', full_res_src)

                        if full_res_src not in image_candidates and full_res_src.startswith('http'):
                            image_candidates.append(full_res_src)

            except Exception as e:
                _logger.warning("Error fetching catalog source %s: %s", url, e)

        return combined_text, image_candidates[:12]

    def _build_catalog_prompt(self, context_text, image_candidates):
        """Construct the prompt enforcing the Stephan's Pet Store catalog formula & safety rules"""
        _, profile = self._detect_brand_profile()
        brand_block = ""
        vet_safety_block = ""
        if profile:
            brand_block = (
                f"\nOFFICIAL BRAND BRAIN ({profile['label']}):\n"
                f"- Official Websites: {', '.join(profile.get('official_urls', []))}\n"
                f"- Brand Guidelines: {profile.get('guidelines', '')}\n"
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
Your task is to analyze the official source catalogue texts, user-supplied keywords, and candidate image URLs below,
and output standardized, factual, healthy, high-converting product data in valid JSON.
{brand_block}{vet_safety_block}
STRICT ACCURACY & HEALTH RULE:
- Ground all ingredients, protein/fat percentages, sizes, and usage instructions strictly in real official brand facts and the reference content below.
- Do NOT hallucinate fake ingredients, fake barcodes, or unverified medical claims.

Reference Content:
{context_text}

Available Image URLs:
{json.dumps(image_candidates, indent=2)}

CRITICAL FORMULA REQUIREMENTS:
All products in Stephan's Pet Store MUST follow the exact same visual hierarchy and sections as seen in our flagship products:
1. title: Clean, standardized format: [Brand] [Product Line / Feature] [Size or Weight] (e.g. 'Bioline Tofu with Bentonite Cat Litter 6L' or 'Summit 10 Cat Complete Chicken and Rice 3kg')
2. barcode: Manufacturer EAN-13 or UPC barcode if detected (e.g. '6970117125535' or empty string).
3. lead_summary: 1-2 compelling executive summary sentences explaining the core formula, technology, and primary benefit.
4. key_highlights: Array of 4 to 6 highlights, each with an icon header and detailed explanation. E.g. [
     {{"header": "⚡ 3-Second Rapid Clumping", "detail": "..."}},
     {{"header": "💧 Ultra Absorbent", "detail": "..."}},
     {{"header": "🌿 99% Dust-Free & Paw-Friendly", "detail": "..."}},
     {{"header": "🛡️ Natural Odor Lock", "detail": "..."}},
     {{"header": "📦 Vacuum-Sealed Freshness", "detail": "..."}}
   ]
5. composition_title: '🧪 Composition & Ingredients' (or '🛠️ Materials & Specifications' for accessories/beds/crates)
6. composition_items: Array of 3 to 6 key components with their functional role. E.g. [
     {{"name": "Natural Bean Dregs (Okara)", "description": "Biodegradable, plant-based absorption base"}},
     {{"name": "Natural Bentonite Clay", "description": "Ultra-fast, hard clumping agent"}},
     {{"name": "Corn Starch", "description": "Natural binding agent"}},
     {{"name": "Guar Gum", "description": "Food-grade pellet stabilizer"}}
   ]
7. instructions_title: '📋 Instructions for Use' (or '📋 Feeding Guide' for pet foods, or '📋 Sizing & Care' for accessories)
8. instructions_steps: Array of 3 to 5 practical, numbered instructions (e.g. preparation, daily maintenance, replacement, cleaning).
9. storage_text: Clear storage advice (e.g. 'Store unopened packs in a cool, dry, well-ventilated area away from direct sunlight and moisture.')
10. key_ingredients_flat: Comma-separated list for backend filters (e.g. 'Natural Bean Dregs (Okara), Natural Bentonite Clay, Corn Starch, Guar Gum').
11. packaging_form: Packaging & physical form (e.g. '6L (~2.5 kg) Vacuum-Sealed Pack | Cylindrical Pellets').
12. plain_description: 2 concise sentences for POS receipts and sales invoices.
13. selected_image_urls: List of up to 3 cleanest high-res URLs from candidate images WITHOUT watermarks or store promotional text.

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
        if gemini_model == 'gemini-2.5-flash':
            gemini_model = 'gemini-2.0-flash'

        # Check preferred provider and fallback
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
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "responseMimeType": "application/json",
                "temperature": 0.2
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
                raise UserError("Google Gemini Authentication Error: Your API key is invalid or unauthorized. Please verify your key at https://aistudio.google.com/app/apikey")
            elif he.code == 429:
                raise UserError("Google Gemini Quota Exceeded (429): Free tier limits reached for this project. Please switch to OpenAI in Settings or enable billing in Google AI Studio.")
            elif he.code == 404:
                raise UserError(f"Google Gemini Model '{model}' not found. Please set model to 'gemini-2.0-flash' or 'gemini-1.5-flash' in Settings.")
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
            "temperature": 0.2
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
                raise UserError("OpenAI Authentication Error (401): The OpenAI API Key is invalid or has been revoked. Please create a new secret key at https://platform.openai.com/api-keys")
            elif he.code == 429:
                raise UserError("OpenAI Quota Exceeded (429): You have run out of API credits on your OpenAI account. Please check your credit balance or switch to Google Gemini.")
            else:
                raise UserError(f"OpenAI API error ({he.code}): {err_content}")
        except Exception as e:
            raise UserError(f"OpenAI API call failed: {e}")

    def _render_stephans_catalog_html(self, data):
        """Render the exact Stephan's Pet Store catalog HTML template formula"""
        title = data.get('title') or self.name
        lead = data.get('lead_summary') or ''
        highlights = data.get('key_highlights') or []
        comp_title = data.get('composition_title') or '🧪 Composition &amp; Ingredients'
        comp_items = data.get('composition_items') or []
        inst_title = data.get('instructions_title') or '📋 Instructions for Use'
        inst_steps = data.get('instructions_steps') or []
        storage = data.get('storage_text') or 'Store in a cool, dry, well-ventilated area away from direct sunlight and humidity.'

        # Highlights items
        highlights_html = ""
        for hl in highlights:
            if isinstance(hl, dict):
                h_header = hl.get('header', '')
                h_detail = hl.get('detail', '')
                highlights_html += f'<li class="py-1"><strong>{h_header}:</strong> {h_detail}</li>\n'
            elif isinstance(hl, str):
                highlights_html += f'<li class="py-1">{hl}</li>\n'

        # Composition items
        comp_html = ""
        for c in comp_items:
            if isinstance(c, dict):
                c_name = c.get('name', '')
                c_desc = c.get('description', '')
                if c_desc:
                    comp_html += f'<li><strong>{c_name}:</strong> {c_desc}</li>\n'
                else:
                    comp_html += f'<li><strong>{c_name}</strong></li>\n'
            elif isinstance(c, str):
                comp_html += f'<li>{c}</li>\n'

        # Instruction steps
        inst_html = ""
        for s in inst_steps:
            inst_html += f'<li>{s}</li>\n'

        html = f"""<div class="container my-4">
    <div class="row">
        <div class="col-12">
            <h3 class="text-primary mb-3">{title}</h3>
            <p class="lead text-muted">
                {lead}
            </p>
            
            <div class="card shadow-sm border-0 mb-4 bg-light">
                <div class="card-body">
                    <h5 class="card-title text-dark font-weight-bold">🌟 Key Product Highlights</h5>
                    <ul class="list-unstyled mb-0">
{highlights_html}
                    </ul>
                </div>
            </div>

            <div class="row mb-4">
                <div class="col-md-6 mb-3">
                    <div class="border rounded p-3 h-100">
                        <h5 class="text-dark">{comp_title}</h5>
                        <ul class="mb-0">
{comp_html}
                        </ul>
                    </div>
                </div>
                <div class="col-md-6 mb-3">
                    <div class="border rounded p-3 h-100">
                        <h5 class="text-dark">{inst_title}</h5>
                        <ol class="mb-0 pl-3">
{inst_html}
                        </ol>
                    </div>
                </div>
            </div>

            <div class="alert alert-info border-0" role="alert">
                <strong>Storage:</strong> {storage}
            </div>
        </div>
    </div>
</div>"""
        return html

    def _apply_ai_data_to_product(self, data):
        """Update product template fields and download clean images"""
        rendered_html = self._render_stephans_catalog_html(data)

        vals = {
            'name': data.get('title') or self.name,
            'description_sale': data.get('plain_description') or False,
            'website_description': rendered_html,
            'x_key_ingredients': data.get('key_ingredients_flat') or False,
            'x_packaging_form': data.get('packaging_form') or False,
        }

        # Set barcode if detected and currently unset
        barcode_val = str(data.get('barcode') or '').strip()
        if barcode_val and not self.barcode:
            vals['barcode'] = barcode_val

        # Download clean watermark-free images (preserve existing studio main photo if already set)
        img_urls = data.get('selected_image_urls', [])
        if img_urls:
            if not self.image_1920:
                main_img_data = self._download_image(img_urls[0])
                if main_img_data:
                    vals['image_1920'] = main_img_data

            # Extra media gallery (only add if product does not already have extra images)
            if not self.product_template_image_ids:
                extra_images = []
                for extra_url in img_urls[1:]:
                    extra_data = self._download_image(extra_url)
                    if extra_data:
                        extra_images.append((0, 0, {
                            'name': f"{self.name} Detail",
                            'image_1920': extra_data
                        }))
                if extra_images:
                    vals['product_template_image_ids'] = extra_images

        self.write(vals)

    def _download_image(self, url):
        """Download remote image and return BinaryBytes or base64 string"""
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=12) as resp:
                raw_bytes = resp.read()
                try:
                    from odoo.orm.fields_binary import BinaryBytes
                    return BinaryBytes(raw_bytes, filename="product.png")
                except ImportError:
                    return base64.b64encode(raw_bytes)
        except Exception as e:
            _logger.warning("Could not download candidate image %s: %s", url, e)
            return False
