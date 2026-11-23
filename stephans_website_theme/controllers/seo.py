import datetime
from hashlib import md5
import logging
import os

from odoo import http
from odoo.http import request
from odoo.addons.website.controllers.main import Website, SITEMAP_CACHE_TIME

_logger = logging.getLogger(__name__)

CANONICAL_DOMAIN = 'https://www.stephanspetstore.co.tz'


class StephansWebsiteSeo(Website):

    @http.route(['/robots.txt'], type='http', auth="public", website=True, multilang=False, sitemap=False)
    def robots(self, **kwargs):
        content = (
            "User-agent: *\n"
            f"Sitemap: {CANONICAL_DOMAIN}/sitemap.xml\n\n"
            "Disallow: /web/login\n"
            "Disallow: /*/web/login\n"
            "Disallow: /web/signup\n"
            "Disallow: /*/web/signup\n"
            "Disallow: /web/reset_password\n"
            "Disallow: /*/web/reset_password\n"
            "Disallow: /my/\n"
            "Disallow: /*/my/*\n"
            "Disallow: /shop/cart\n"
            "Disallow: /*/shop/cart\n"
            "Disallow: /shop/checkout\n"
            "Disallow: /*/shop/checkout\n"
            "Disallow: /shop/payment\n"
            "Disallow: /*/shop/payment\n"
            "Disallow: /shop/confirmation\n"
            "Disallow: /*/shop/confirmation\n\n"
            "# Legacy duplicate and preview routes\n"
            "Disallow: /stephans-preview\n"
            "Disallow: /stephans-grooming\n"
            "Disallow: /contactus\n"
            "Disallow: /faqs\n"
        )
        return request.make_response(content, [('Content-Type', 'text/plain; charset=utf-8')])

    @http.route('/sitemap.xml', type='http', auth="public", website=True, multilang=False, sitemap=False)
    def sitemap_xml_index(self, **kwargs):
        Attachment = request.env['ir.attachment'].sudo()
        mimetype = 'application/xml;charset=utf-8'
        url_root = CANONICAL_DOMAIN + '/'
        hashed_url_root = md5(url_root.encode()).hexdigest()[:8]
        sitemap_base_url = '/sitemap-%d-%s' % (request.env.website.id, hashed_url_root)

        # Check existing cached HTTPS sitemap
        dom = [('url', '=', '%s.xml' % sitemap_base_url), ('type', '=', 'binary')]
        sitemap = Attachment.search(dom, limit=1)
        if sitemap and sitemap.create_date:
            create_date = sitemap.create_date
            if isinstance(create_date, str):
                create_date = datetime.datetime.fromisoformat(create_date)
            if (datetime.datetime.now() - create_date) < SITEMAP_CACHE_TIME:
                raw_content = sitemap.raw
                if isinstance(raw_content, bytes):
                    content = raw_content.decode('utf-8', errors='ignore')
                else:
                    content = str(raw_content)
                if content and 'http://www.stephanspetstore.co.tz' not in content:
                    return request.make_response(content, [('Content-Type', mimetype)])

        # Clear out any legacy sitemaps
        Attachment.search([('type', '=', 'binary'), ('url', '=like', '/sitemap-%')]).unlink()

        # Enumerate pages
        locs = list(request.env.website.with_user(request.env.website.user_id)._enumerate_pages(ignore_custom_homepage=True))

        excluded = {'/stephans-preview', '/stephans-grooming', '/contactus', '/faqs'}
        clean_locs = []
        seen = set()

        for loc in locs:
            path = loc.get('loc', '')
            if path in excluded:
                continue
            if path in seen:
                continue
            seen.add(path)
            clean_locs.append(loc)

        # Include dedicated store landing pages
        for store_path in ('/stores/masaki', '/stores/mikocheni'):
            if store_path not in seen:
                clean_locs.append({
                    'loc': store_path,
                    'priority': 0.8,
                    'changefreq': 'weekly',
                })
                seen.add(store_path)

        values = {
            'locs': clean_locs,
            'url_root': CANONICAL_DOMAIN,
        }
        urls = request.env.website._render_template('website.sitemap_locs', values)
        content = request.env.website._render_template('website.sitemap_xml', {'content': urls})

        # Ensure every loc has https scheme
        content = content.replace('http://www.stephanspetstore.co.tz', CANONICAL_DOMAIN)

        Attachment.create({
            'raw': content.encode('utf-8'),
            'mimetype': mimetype,
            'type': 'binary',
            'name': '%s.xml' % sitemap_base_url,
            'url': '%s.xml' % sitemap_base_url,
        })
        return request.make_response(content, [('Content-Type', mimetype)])

    @http.route(['/og-image.jpg', '/og-image.png'], type='http', auth='public', website=True, sitemap=False)
    def og_image(self, **kwargs):
        """Serve the dedicated 1200x630 branded OpenGraph share banner."""
        img_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'static', 'src', 'images', 'branding', 'og-image.jpg'
        )
        if os.path.isfile(img_path):
            with open(img_path, 'rb') as f:
                content = f.read()
            resp = request.make_response(content, [
                ('Content-Type', 'image/jpeg'),
                ('Cache-Control', 'public, max-age=604800, immutable'),
                ('Access-Control-Allow-Origin', '*'),
            ])
            # Strip CSP restriction so social crawlers (WhatsApp, Facebook) load image without policy interference
            if 'Content-Security-Policy' in resp.headers:
                del resp.headers['Content-Security-Policy']
            return resp
        return request.redirect(f'{CANONICAL_DOMAIN}/stephans_website_theme/static/src/images/hero/hero-stephans.jpg', code=301)

    @http.route('/llms.txt', type='http', auth='public', website=True, multilang=False, sitemap=False)
    def llms_txt(self):
        """Serve authoritative LLM knowledge context for generative engine optimization."""
        txt_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'static', 'llms.txt'
        )
        if os.path.isfile(txt_path):
            with open(txt_path, 'r', encoding='utf-8') as f:
                content = f.read()
        else:
            content = "# Stephan's Pet Store\nPremier pet store & grooming studio in Dar es Salaam, Tanzania."

        return request.make_response(content, [
            ('Content-Type', 'text/plain; charset=utf-8'),
            ('Cache-Control', 'public, max-age=86400'),
        ])

    @http.route(['/stephans-preview'], type='http', auth='public', website=True, sitemap=False)
    def redirect_preview(self, **kw):
        return request.redirect('/', code=301)

    @http.route(['/stephans-grooming'], type='http', auth='public', website=True, sitemap=False)
    def redirect_grooming(self, **kw):
        return request.redirect('/grooming', code=301)

    @http.route(['/contactus'], type='http', auth='public', website=True, sitemap=False)
    def redirect_contactus(self, **kw):
        return request.redirect('/contact', code=301)

    @http.route(['/faqs'], type='http', auth='public', website=True, sitemap=False)
    def redirect_faqs(self, **kw):
        return request.redirect('/faq', code=301)

    @http.route('/stores/masaki', type='http', auth='public', website=True, sitemap=True)
    def store_masaki(self, **kw):
        return request.render('stephans_website_theme.store_masaki_page', {
            'additional_title': "Stephan's Pet Store Masaki (Slipway) | Pet Shop & Grooming Dar es Salaam",
            'meta_description': "Visit Stephan's Pet Store in Masaki at 11 Slipway Road. Premium pet food, toys, accessories, and full-service dog & cat grooming studio. Open Mon–Sat 9:00 AM – 8:30 PM.",
        })

    @http.route('/stores/mikocheni', type='http', auth='public', website=True, sitemap=True)
    def store_mikocheni(self, **kw):
        return request.render('stephans_website_theme.store_mikocheni_page', {
            'additional_title': "Stephan's Pet Store Mikocheni | Pet Supplies & Food Dar es Salaam",
            'meta_description': "Visit Stephan's Pet Store in Mikocheni at 59 Mikocheni A. Comprehensive pet food, grooming supplies, veterinary essentials, and accessories. Open Mon–Sat 9:00 AM – 6:00 PM.",
        })
