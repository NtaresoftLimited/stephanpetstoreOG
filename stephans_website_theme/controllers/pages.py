# -*- coding: utf-8 -*-
import json
from odoo import http
from odoo.http import request
from markupsafe import Markup, escape


PAGES = {
    'about': {
        'kicker': 'Our story', 'title': "A pet store built around care.",
        'intro': "Stephan's Pet Store is Tanzania's trusted destination for premium pet food, thoughtful accessories and professional grooming.",
        'image': '/stephans_website_theme/static/src/images/pages/stephan.png',
        'sections': [
            ('More than a pet store', "We believe pets are family. Every product we stock and every service we offer is selected to help pets live happier, healthier lives."),
            ('Thoughtfully selected', 'Our shelves bring together dependable nutrition, practical essentials, toys and accessories chosen for quality and value.'),
            ('Professional grooming', 'Our experienced grooming team provides calm, careful appointments tailored to each pet and their individual needs.'),
        ],
    },
    'contact': {
        'kicker': 'Get in touch', 'title': "We're here to help.",
        'intro': 'Questions about products, an order or grooming? Speak with the Stephan’s team by phone, email or WhatsApp.',
        'sections': [
            ('Call us', '+255 786 627 873\n+255 769 324 445'),
            ('Email', 'info@stephanspetstore.co.tz'),
            ('Opening hours', 'Monday–Friday: 9:00 AM–8:30 PM\nSaturday: 10:00 AM–8:30 PM\nSunday: Closed'),
        ],
    },
    'stores': {
        'kicker': 'Store locator', 'title': 'Visit Stephan’s.',
        'intro': 'Find premium pet products and friendly help at our Dar es Salaam locations in Masaki and Mikocheni.',
        'image': '/stephans_website_theme/static/src/images/pages/stores-banner.png',
        'sections': [
            ('Masaki', '11 Slipway Road, Masaki, Dar es Salaam\n+255 786 627 873'),
            ('Mikocheni', '59 Mikocheni A, Dar es Salaam\n+255 769 324 445'),
        ],
    },
    'allbrands': {
        'kicker': 'Our brands', 'title': 'Exceptional brands, thoughtfully selected.',
        'intro': 'Explore trusted pet-care and nutrition brands selected for quality, safety and everyday wellbeing.',
        'brands': [
            ('Bioline', 'Bioline.webp', '/brands/bioline'),
            ('Summit 10', 'Summit-10.svg', '/brands/summit-10'),
            ('TropiCat', 'TropiCat_logo.svg', '/brands/tropicat'),
            ('TropiDog', 'TropiDog_logo.svg', '/brands/tropidog'),
            ('Josera', None, '/brands/josera'),
            ('Bravecto', None, '/brands/bravecto'),
        ],
        'sections': [],
    },
    'faq': {
        'kicker': 'Help centre', 'title': 'Frequently asked questions.',
        'intro': 'Answers to common questions about shopping, delivery, returns and grooming.',
        'sections': [
            ('Do you deliver in Dar es Salaam?', 'Yes! We deliver across all Dar es Salaam districts (Masaki, Mikocheni, Oysterbay, Kinondoni, Upanga, etc.) with free delivery on orders over 100,000 TZS.'),
            ('How can I book grooming?', 'Use our online Grooming page or contact us on WhatsApp (+255 769 324 445) to select your pet, preferred package, branch, date and time.'),
            ('Which payment methods do you accept?', 'We accept Selcom Mobile Money (M-Pesa, Mixx by Yas, Airtel Money, Halopesa), Visa/Mastercard, Sky Wallet store credit, and Cash on delivery/store pickup.'),
            ('Can I return an item?', 'Eligible defective or incorrect items in original packaging may be returned under our Returns policy within 7 days.'),
        ],
    },
    'grooming-policy': {
        'kicker': 'Grooming studio', 'title': 'Grooming policy.',
        'intro': 'These guidelines keep every pet safe, comfortable and cared for throughout their appointment.',
        'sections': [
            ('Before your appointment', 'Please disclose medical conditions, allergies and behavioural concerns. Arrive approximately ten minutes early for check-in.'),
            ('During grooming', 'Every pet and every coat is different. Tangled or matted coats require extra time and careful attention. Additional care and fees (Moderate Detangling TSh 100,000, Intensive Detangling TSh 150,000, Handling Fee TSh 50,000, Sedation Fee TSh 50,000) will be discussed and agreed with you before proceeding.'),
            ('Pickup', 'We will contact you when grooming is complete. Please collect your pet within one hour. After this, a late pickup fee of TSh 20,000 per hour applies when collection is delayed beyond this window.'),
            ('Cancellations', 'Please tell us as early as possible when you need to reschedule or cancel an appointment.'),
        ],
    },
    'return-policy': {
        'kicker': 'Customer care', 'title': 'Returns and exchanges.',
        'intro': 'We want every Stephan’s purchase to reach you in the correct condition.',
        'sections': [
            ('Eligible returns', 'Contact us promptly if an item is defective, damaged or different from what you ordered. Keep the receipt and original packaging.'),
            ('Non-returnable items', 'Opened food, hygiene products, medicines and personalised or used items cannot normally be returned unless defective.'),
            ('How to request a return', 'Contact our team with your receipt, order details and clear photos where applicable. We will review and advise the next step.'),
        ],
    },
    'terms': {
        'kicker': 'Legal', 'title': 'Terms and conditions.',
        'intro': 'These terms apply when using Stephan’s Pet Store services and purchasing products from us.',
        'sections': [
            ('Orders and availability', 'Orders remain subject to product availability and confirmation. We may contact you if an item or price requires correction.'),
            ('Payments', 'Payment must be completed using an accepted method. Prices are displayed in Tanzanian shillings (TZS).'),
            ('Delivery and collection', 'Delivery times are estimates and depend on location and availability. Please provide accurate contact and address details.'),
            ('Privacy', 'Customer information is used to process orders, appointments and support requests in accordance with applicable requirements.'),
        ],
    },
    'blog': {
        'kicker': 'Pet journal', 'title': 'Care, knowledge and stories.',
        'intro': 'Practical guidance from Stephan’s for happy pets and confident pet parents.',
        'sections': [
            ('10 essential tips for first-time dog owners', 'A simple guide to preparing your home, routines and care for a new dog.'),
            ("Understanding your cat's body language", 'Learn how posture, ears, eyes and tail movements reveal how your cat feels.'),
            ('The benefits of regular pet grooming', 'How coat, nail, ear and skin care support comfort and long-term wellbeing.'),
            ('Choosing the right food for your pet', 'Consider life stage, size, activity and individual health needs when choosing nutrition.'),
            ('Creating a bird-friendly home', 'Safe positioning, enrichment and daily care for companion birds.'),
            ('Aquarium maintenance 101', 'Build a consistent routine for water quality, cleaning and healthy aquatic life.'),
        ],
    },
    'delivery': {
        'kicker': 'Delivery', 'title': 'Pet essentials, brought to you.',
        'intro': 'We arrange delivery across Dar es Salaam and can advise on options for other locations in Tanzania.',
        'sections': [
            ('Dar es Salaam delivery', 'Fast delivery across Dar es Salaam. Free delivery on orders over 100,000 TZS. Standard orders delivered within 2-4 hours.'),
            ('Before dispatch', 'Our team may contact you to confirm your address, phone number, items and payment details.'),
            ('Need an update?', 'Contact us by phone (+255 786 627 873) or WhatsApp (+255 769 324 445) with your order reference for instant tracking.'),
        ],
    },
}

BRANDS_DATA = {
    'bioline': {
        'name': 'Bioline',
        'kicker': 'Natural Pet Care',
        'description': 'Natural and eco-friendly pet care, hygiene, and grooming solutions crafted for pets of all life stages.',
        'logo': '/stephans_website_theme/static/src/images/brands/Bioline.webp',
        'keywords': ['bioline'],
    },
    'summit-10': {
        'name': 'Summit 10',
        'kicker': 'Premium Nutrition',
        'description': 'High-performance holistic nutrition formulated with fresh meats, natural superfoods, and balanced nutrients.',
        'logo': '/stephans_website_theme/static/src/images/brands/Summit-10.svg',
        'keywords': ['summit 10', 'summit10'],
    },
    'summit10': {
        'name': 'Summit 10',
        'kicker': 'Premium Nutrition',
        'description': 'High-performance holistic nutrition formulated with fresh meats, natural superfoods, and balanced nutrients.',
        'logo': '/stephans_website_theme/static/src/images/brands/Summit-10.svg',
        'keywords': ['summit 10', 'summit10'],
    },
    'tropidog': {
        'name': 'TropiDog',
        'kicker': 'Complete Dog Nutrition',
        'description': 'Super premium and premium nutrition tailored for puppies, adult, and senior dogs across all breeds.',
        'logo': '/stephans_website_theme/static/src/images/brands/TropiDog_logo.svg',
        'keywords': ['tropidog'],
    },
    'tropicat': {
        'name': 'TropiCat',
        'kicker': 'Balanced Feline Care',
        'description': 'Scientifically formulated nutrition to support urinary health, shiny coats, and vitality in cats and kittens.',
        'logo': '/stephans_website_theme/static/src/images/brands/TropiCat_logo.svg',
        'keywords': ['tropicat'],
    },
    'josera': {
        'name': 'Josera',
        'kicker': 'German Super Premium',
        'description': 'Certified German pet food crafted with sustainable, climate-neutral ingredients and zero artificial preservatives.',
        'logo': None,
        'keywords': ['josera'],
    },
    'bravecto': {
        'name': 'Bravecto',
        'kicker': 'Veterinary Protection',
        'description': 'Long-lasting veterinary tick and flea protection chewables and spot-ons for dogs and cats.',
        'logo': None,
        'keywords': ['bravecto'],
    },
    'whiskas': {
        'name': 'Whiskas',
        'kicker': 'Delicious Feline Meals',
        'description': 'Nutritious wet and dry meals specially designed to bring happiness and energy to cats.',
        'logo': None,
        'keywords': ['whiskas'],
    },
    'beeno': {
        'name': 'Beeno',
        'kicker': 'Tasty Dog Treats',
        'description': 'Delicious, nutritious reward biscuits and treats to support dental health and positive training.',
        'logo': None,
        'keywords': ['beeno'],
    },
    'ownat': {
        'name': 'Ownat',
        'kicker': 'Fresh Meat Nutrition',
        'description': 'Natural ingredients and fresh meat recipes designed for dogs and cats with high nutritional standards.',
        'logo': None,
        'keywords': ['ownat'],
    },
}


class StephansWebsitePages(http.Controller):
    @http.route(['/about', '/allbrands', '/faq', '/grooming-policy', '/return-policy', '/terms', '/blog', '/delivery'], type='http', auth='public', website=True, sitemap=True)
    def content_page(self, **kw):
        key = request.httprequest.path.strip('/') or 'about'
        if key == 'faqs':
            key = 'faq'
        return request.render('stephans_website_theme.content_page', {
            'page': PAGES[key],
            'page_key': key,
            'additional_title': PAGES[key]['title'],
            'meta_description': PAGES[key]['intro'],
        })

    @http.route(['/brands/<string:slug>', '/brand/<string:slug>'], type='http', auth='public', website=True, sitemap=True)
    def brand_page(self, slug, **kw):
        slug_key = slug.lower().strip()
        brand_info = BRANDS_DATA.get(slug_key)
        if not brand_info:
            brand_name = slug_key.replace('-', ' ').title()
            brand_info = {
                'name': brand_name,
                'kicker': 'Featured Brand',
                'description': f'Discover authentic pet products from {brand_name} at Stephan’s Pet Store Tanzania.',
                'logo': None,
                'keywords': [slug_key.replace('-', ' ')],
            }

        # Query products matching this brand
        domain = [('active', '=', True), ('is_published', '=', True)]
        kw_domains = []
        for term in brand_info['keywords']:
            kw_domains.append(('name', 'ilike', term))
            kw_domains.append(('default_code', 'ilike', term))
        
        if kw_domains:
            combined_domain = ['|'] * (len(kw_domains) - 1) + kw_domains
            domain.extend(combined_domain)

        products = request.env['product.template'].sudo().search(domain, order='list_price desc, name asc', limit=48)
        currency = request.env.company.currency_id

        product_cards = []
        for p in products:
            product_cards.append({
                'id': p.id,
                'name': p.name,
                'price_formatted': currency.format(p.list_price) if currency else f"{p.list_price:,.0f} TZS",
                'url': p.website_url or f"/shop/product/{p.id}",
                'image_url': f"/web/image/product.template/{p.id}/image_512",
                'category': p.categ_id.name if p.categ_id else '',
            })

        return request.render('stephans_website_theme.brand_page', {
            'brand': brand_info,
            'slug': slug_key,
            'products': product_cards,
            'additional_title': f"{brand_info['name']} Pet Products & Food Tanzania",
            'meta_description': brand_info['description'],
        })

    @http.route('/stores', type='http', auth='public', website=True, sitemap=True)
    def stores_page(self, **kw):
        return request.render('stephans_website_theme.stores_page', {
            'additional_title': "Pet Stores in Dar es Salaam",
            'meta_description': "Find Stephan's Pet Store locations in Masaki and Mikocheni, Dar es Salaam, with opening hours, contacts and directions.",
        })

    @http.route('/contact', type='http', auth='public', website=True, sitemap=True)
    def contact_page(self, **kw):
        return request.render('stephans_website_theme.contact_page', {
            'contact_sent': kw.get('sent') == '1',
            'contact_error': kw.get('error') == '1',
            'additional_title': "Contact Stephan's Pet Store",
            'meta_description': "Contact Stephan's Pet Store in Dar es Salaam by phone, WhatsApp or email, find our locations, or book professional pet grooming.",
        })

    @http.route('/contact/send', type='http', auth='public', website=True, methods=['POST'], csrf=True)
    def contact_send(self, **post):
        name = (post.get('name') or '').strip()[:120]
        email = (post.get('email') or '').replace('\r', '').replace('\n', '').strip()[:254]
        message = (post.get('message') or '').strip()[:5000]
        if not name or '@' not in email or not message:
            return request.redirect('/contact?error=1')

        company = request.env.company
        recipient = company.email or 'info@stephanspetstore.co.tz'
        body = Markup(
            '<p><strong>Name:</strong> %s</p>'
            '<p><strong>Email:</strong> %s</p>'
            '<p><strong>Message:</strong></p><p>%s</p>'
        ) % (escape(name), escape(email), escape(message).replace('\n', Markup('<br/>')))
        request.env['mail.mail'].sudo().create({
            'subject': 'Website contact: %s' % name,
            'body_html': body,
            'email_from': recipient,
            'reply_to': email,
            'email_to': recipient,
        })
        return request.redirect('/contact?sent=1')

    # Instant Global Predictive Search API (JSON for SearchModal)
    @http.route('/stephans/api/search', type='http', auth='public', website=True, csrf=False, methods=['GET', 'POST'])
    def api_search(self, **kw):
        import unicodedata

        def strip_accents(s):
            if not s:
                return ''
            return ''.join(c for c in unicodedata.normalize('NFD', s) if unicodedata.category(c) != 'Mn')

        clean_q = (kw.get('q') or kw.get('query') or '').strip()
        if not clean_q and request.httprequest.data:
            try:
                body = json.loads(request.httprequest.data.decode('utf-8'))
                clean_q = (body.get('q') or body.get('query') or '').strip()
            except Exception:
                pass

        if not clean_q or len(clean_q) < 2:
            return request.make_json_response({'results': [], 'count': 0})

        pt_model = request.env['product.template'].sudo()
        available_fields = pt_model._fields
        limit_count = int(kw.get('limit', 10))

        # 1. Multi-term Tokenization (e.g. 'Summit 10 Paté Delish Chicken 400g')
        raw_tokens = clean_q.split()

        sub_domains = []
        for token in raw_tokens:
            tok = token.strip()
            if not tok:
                continue
            tok_unaccent = strip_accents(tok)

            or_clauses = [
                ('name', 'ilike', tok),
                ('default_code', 'ilike', tok),
                ('description_sale', 'ilike', tok),
            ]
            if tok_unaccent.lower() != tok.lower():
                or_clauses.extend([
                    ('name', 'ilike', tok_unaccent),
                    ('description_sale', 'ilike', tok_unaccent),
                ])

            if 'barcode' in available_fields:
                or_clauses.append(('barcode', 'ilike', tok))
            if 'x_keywords' in available_fields:
                or_clauses.append(('x_keywords', 'ilike', tok))
                if tok_unaccent.lower() != tok.lower():
                    or_clauses.append(('x_keywords', 'ilike', tok_unaccent))
            if 'x_key_ingredients' in available_fields:
                or_clauses.append(('x_key_ingredients', 'ilike', tok))
            if 'x_packaging_form' in available_fields:
                or_clauses.append(('x_packaging_form', 'ilike', tok))
            if 'public_categ_ids' in available_fields:
                or_clauses.append(('public_categ_ids.name', 'ilike', tok))

            tok_domain = []
            for _ in range(len(or_clauses) - 1):
                tok_domain.append('|')
            tok_domain.extend(or_clauses)
            sub_domains.append(tok_domain)

        # Full AND condition: every search term must be represented
        full_domain = [('active', '=', True), ('is_published', '=', True)]
        for sd in sub_domains:
            full_domain.extend(sd)

        products = list(pt_model.search(full_domain, order='list_price desc', limit=limit_count * 2))

        # 2. Smart Fallback: if strict full-token match is empty, search ANY matching token
        if not products and len(raw_tokens) > 1:
            fallback_or = []
            for token in raw_tokens:
                tok = token.strip()
                if len(tok) < 2:
                    continue
                fallback_or.append(('name', 'ilike', tok))
                tok_u = strip_accents(tok)
                if tok_u.lower() != tok.lower():
                    fallback_or.append(('name', 'ilike', tok_u))
                if 'default_code' in available_fields:
                    fallback_or.append(('default_code', 'ilike', tok))

            if fallback_or:
                any_domain = [('active', '=', True), ('is_published', '=', True)]
                for _ in range(len(fallback_or) - 1):
                    any_domain.append('|')
                any_domain.extend(fallback_or)
                products = list(pt_model.search(any_domain, order='list_price desc', limit=limit_count * 2))

        # 3. Sort by relevance to query (highest keyword overlap first)
        def relevance_score(prod):
            score = 0
            n = (prod.name or '').lower()
            code = (prod.default_code or '').lower()
            for tok in raw_tokens:
                tl = tok.lower()
                if tl in n:
                    score += 10
                if tl in code:
                    score += 5
            return score

        products = sorted(products, key=relevance_score, reverse=True)[:limit_count]

        currency = request.env.company.currency_id
        results = []
        for p in products:
            cat_name = ''
            if hasattr(p, 'public_categ_ids') and p.public_categ_ids:
                cat_name = p.public_categ_ids[0].name
            elif p.categ_id:
                cat_name = p.categ_id.name

            brand_name = ''
            if hasattr(p, 'product_brand_id') and p.product_brand_id:
                brand_name = p.product_brand_id.name
            elif hasattr(p, 'brand_id') and p.brand_id:
                brand_name = p.brand_id.name

            results.append({
                'id': p.id,
                'name': p.name,
                'price': p.list_price,
                'price_formatted': currency.format(p.list_price) if currency else f"{p.list_price:,.0f} TZS",
                'url': p.website_url or f"/shop/product/{p.id}",
                'image_url': f"/web/image/product.template/{p.id}/image_128",
                'category': cat_name or 'Pet Food',
                'brand': brand_name or 'Summit10' if 'summit' in p.name.lower() else (brand_name or ''),
                'default_code': p.default_code or '',
            })

        # Collect matched categories
        matched_categories = []
        seen_cats = set()
        for p in products:
            c = p.categ_id
            if c:
                prefix = 'Cats' if ('cat' in (p.name or '').lower()) else 'Dogs'
                c_name = f"{prefix} > {c.name}"
                if c_name not in seen_cats:
                    seen_cats.add(c_name)
                    matched_categories.append({
                        'name': c_name,
                        'url': f"/shop?search={c.name}",
                        'type': 'Category'
                    })
            if len(matched_categories) >= 2:
                break

        if not matched_categories:
            q_lower = clean_q.lower()
            if 'cat' in q_lower or 'kitten' in q_lower or 'pate' in q_lower:
                matched_categories.append({'name': 'Cats > Wet Food', 'url': '/shop?search=Cat+Food', 'type': 'Category'})
            elif 'dog' in q_lower or 'puppy' in q_lower:
                matched_categories.append({'name': 'Dogs > Food', 'url': '/shop?search=Dog+Food', 'type': 'Category'})

        # Collect matched brands
        matched_brands = []
        KNOWN_BRANDS = [
            {'name': 'Summit10', 'url': '/brands/summit10'},
            {'name': 'Bioline', 'url': '/brands/bioline'},
            {'name': 'TropiDog', 'url': '/brands/tropidog'},
            {'name': 'TropiCat', 'url': '/brands/tropicat'},
            {'name': 'Josera', 'url': '/brands/josera'},
            {'name': 'Bravecto', 'url': '/brands/bravecto'},
            {'name': 'Ownat', 'url': '/brands/ownat'},
            {'name': 'Whiskas', 'url': '/brands/whiskas'},
            {'name': 'NexGard', 'url': '/brands/nexgard'},
        ]
        q_norm = strip_accents(clean_q).lower()
        for b in KNOWN_BRANDS:
            b_norm = strip_accents(b['name']).lower()
            if b_norm in q_norm or any(tok.lower() in b_norm for tok in raw_tokens if len(tok) >= 3):
                matched_brands.append(b)

        return request.make_json_response({
            'results': results,
            'products': results,
            'categories': matched_categories[:2],
            'brands': matched_brands[:2],
            'count': len(results)
        })

    # Slide-over Cart Drawer Status API
    @http.route('/stephans/api/cart_status', type='http', auth='public', website=True, csrf=False, methods=['GET', 'POST'])
    def api_cart_status(self, **kw):
        website = getattr(request, 'website', None)
        if not website and hasattr(request, 'env') and 'website' in request.env:
            try:
                website = request.env['website'].get_current_website()
            except Exception:
                website = None

        order = None
        if website and hasattr(website, 'sale_get_order'):
            try:
                order = website.sale_get_order()
            except Exception:
                order = None

        if not order and hasattr(request, 'session') and request.session.get('sale_order_id'):
            try:
                so = request.env['sale.order'].sudo().browse(request.session['sale_order_id'])
                if so.exists() and so.state == 'draft':
                    order = so
            except Exception:
                order = None

        if not order:
            return request.make_json_response({
                'lines': [],
                'items': [],
                'cart_quantity': 0,
                'item_count': 0,
                'amount_total': 0.0,
                'amount_formatted': '0 TZS',
                'free_delivery_threshold': 100000.0,
                'free_delivery_remaining': 100000.0,
                'has_free_delivery': False,
            })

        currency = order.currency_id
        lines = []
        for line in order.order_line:
            if line.product_uom_qty <= 0:
                continue
            lines.append({
                'id': line.id,
                'line_id': line.id,
                'product_id': line.product_id.id,
                'name': line.product_id.name or line.name,
                'quantity': int(line.product_uom_qty),
                'qty': int(line.product_uom_qty),
                'price_unit': line.price_unit,
                'price_subtotal': line.price_subtotal,
                'price_unit_formatted': currency.format(line.price_unit) if currency else f"{line.price_unit:,.0f} TZS",
                'price_formatted': currency.format(line.price_subtotal) if currency else f"{line.price_subtotal:,.0f} TZS",
                'image_url': f"/web/image/product.product/{line.product_id.id}/image_128",
                'url': line.product_id.product_tmpl_id.website_url or f"/shop/product/{line.product_id.product_tmpl_id.id}",
            })

        total = order.amount_total or 0.0
        free_thresh = 100000.0
        remaining = max(0.0, free_thresh - total)
        qty_count = int(sum(i['quantity'] for i in lines))

        return request.make_json_response({
            'lines': lines,
            'items': lines,
            'cart_quantity': qty_count,
            'item_count': qty_count,
            'amount_total': total,
            'amount_formatted': currency.format(total) if currency else f"{total:,.0f} TZS",
            'free_delivery_threshold': free_thresh,
            'free_delivery_remaining': remaining,
            'has_free_delivery': remaining <= 0,
        })

    # Cart Drawer Quantity Update API
    @http.route('/stephans/api/cart_update', type='http', auth='public', website=True, csrf=False, methods=['POST'])
    def api_cart_update(self, **kw):
        line_id = kw.get('line_id')
        quantity = kw.get('quantity')
        if (line_id is None or quantity is None) and request.httprequest.data:
            try:
                body = json.loads(request.httprequest.data.decode('utf-8'))
                line_id = body.get('line_id')
                quantity = body.get('quantity')
            except Exception:
                pass

        try:
            line_id = int(line_id) if line_id is not None else None
            quantity = int(quantity) if quantity is not None else None
        except (ValueError, TypeError):
            pass

        website = getattr(request, 'website', None)
        if not website and hasattr(request, 'env') and 'website' in request.env:
            try:
                website = request.env['website'].get_current_website()
            except Exception:
                website = None

        order = None
        if website and hasattr(website, 'sale_get_order'):
            try:
                order = website.sale_get_order(force_create=False)
            except Exception:
                order = None

        if not order and hasattr(request, 'session') and request.session.get('sale_order_id'):
            try:
                so = request.env['sale.order'].sudo().browse(request.session['sale_order_id'])
                if so.exists() and so.state == 'draft':
                    order = so
            except Exception:
                order = None

        if order and line_id is not None:
            line = order.order_line.filtered(lambda l: l.id == line_id)
            if line:
                if quantity is not None and quantity <= 0:
                    line.unlink()
                elif quantity is not None:
                    line.product_uom_qty = quantity

        return self.api_cart_status()

    @http.route(['/shop/dogs', '/shop/cats', '/shop/small-pets', '/shop/pet-food', '/shop/accessories'], type='http', auth='public', website=True)
    def shop_alias(self, **kw):
        term = request.httprequest.path.rsplit('/', 1)[-1].replace('-', ' ')
        return request.redirect('/shop?search=' + term)

    @http.route('/cart', type='http', auth='public', website=True)
    def cart_alias(self, **kw):
        return request.redirect('/shop/cart')

    @http.route(['/google-merchant-feed.xml', '/merchant-feed.xml'], type='http', auth='public', website=True, csrf=False)
    def google_merchant_feed(self, **kw):
        """Official Google Merchant Center RSS 2.0 Product Feed."""
        base_url = "https://www.stephanspetstore.co.tz"
        try:
            website = getattr(request, 'website', None)
            if not website and hasattr(request, 'env') and 'website' in request.env:
                website = request.env['website'].get_current_website()
            if website and website.domain:
                d = website.domain.strip().rstrip('/')
                if not d.startswith('http'):
                    base_url = f"https://{d}"
                elif d.startswith('http://'):
                    base_url = f"https://{d[7:]}"
                else:
                    base_url = d
        except Exception:
            base_url = "https://www.stephanspetstore.co.tz"
        domain = [
            ('sale_ok', '=', True),
            ('active', '=', True),
            ('is_published', '=', True),
            ('list_price', '>', 0),
        ]
        products = request.env['product.template'].sudo().search(domain, order='name asc', limit=2500)

        items_xml = []
        for p in products:
            p_name = escape((p.name or '').strip())
            raw_desc = (p.description_sale or '').strip()
            if not raw_desc:
                raw_desc = f"Buy {(p.name or '').strip()} at Stephan's Pet Store in Dar es Salaam, Tanzania. Premium pet food, accessories, and supplies available at Slipway Masaki and Mikocheni branches with fast local delivery across Dar es Salaam."
            desc = escape(raw_desc[:4900])

            p_link = f"{base_url}{p.website_url}" if p.website_url else f"{base_url}/shop/product/{p.id}"
            img_link = f"{base_url}/web/image/product.template/{p.id}/image_1024"

            brand = "Stephan's Pet Store"
            if hasattr(p, 'product_brand_id') and p.product_brand_id and p.product_brand_id.name:
                brand = p.product_brand_id.name.strip()
            elif hasattr(p, 'brand_id') and p.brand_id and p.brand_id.name:
                brand = p.brand_id.name.strip()
            brand = escape(brand)

            availability = "in_stock" if getattr(p, 'qty_available', 1.0) > 0 else "out_of_stock"
            price_str = f"{p.list_price:.2f} TZS"

            cat_name = p.categ_id.name.strip() if p.categ_id and p.categ_id.name else "Pet Supplies"
            google_cat = "Animals &amp; Pet Supplies &gt; Pet Supplies"
            upper_cat = cat_name.upper()
            if "DOG" in upper_cat:
                google_cat = "Animals &amp; Pet Supplies &gt; Pet Supplies &gt; Dog Supplies"
            elif "CAT" in upper_cat:
                google_cat = "Animals &amp; Pet Supplies &gt; Pet Supplies &gt; Cat Supplies"
            elif "BIRD" in upper_cat:
                google_cat = "Animals &amp; Pet Supplies &gt; Pet Supplies &gt; Bird Supplies"

            sku = escape(str(p.default_code or f"PROD-{p.id}"))

            item = f"""    <item>
      <g:id>{sku}</g:id>
      <g:title>{p_name}</g:title>
      <g:description>{desc}</g:description>
      <g:link>{p_link}</g:link>
      <g:image_link>{img_link}</g:image_link>
      <g:availability>{availability}</g:availability>
      <g:price>{price_str}</g:price>
      <g:brand>{brand}</g:brand>
      <g:condition>new</g:condition>
      <g:google_product_category>{google_cat}</g:google_product_category>
    </item>"""
            items_xml.append(item)

        xml_body = "\n".join(items_xml)
        xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<rss xmlns:g="http://base.google.com/ns/1.0" version="2.0">
  <channel>
    <title>Stephan's Pet Store - Google Merchant Feed</title>
    <link>{base_url}</link>
    <description>Official Google Merchant Center Product Feed for Stephan's Pet Store Dar es Salaam (Slipway Masaki and Mikocheni branches)</description>
{xml_body}
  </channel>
</rss>"""
        return request.make_response(
            xml_content,
            headers=[
                ('Content-Type', 'application/xml; charset=utf-8'),
                ('Cache-Control', 'public, max-age=3600'),
            ]
        )
