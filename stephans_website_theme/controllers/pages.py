from odoo import http
from odoo.http import request


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
        'intro': 'Find premium pet products and friendly help at our Dar es Salaam locations.',
        'image': '/stephans_website_theme/static/src/images/pages/stores-banner.png',
        'sections': [
            ('Masaki', '11 Slipway Road, Masaki, Dar es Salaam\n+255 786 627 873'),
            ('Mikocheni', '59 Mikocheni A, Dar es Salaam\n+255 769 324 445'),
        ],
    },
    'allbrands': {
        'kicker': 'Our brands', 'title': 'Exceptional brands, thoughtfully selected.',
        'intro': 'Explore trusted pet-care and nutrition brands selected for quality, safety and everyday wellbeing.',
        'brands': [('Bioline', 'Bioline.webp'), ('Summit 10', 'Summit-10.svg'), ('TropiCat', 'TropiCat_logo.svg'), ('TropiDog', 'TropiDog_logo.svg')],
        'sections': [],
    },
    'faq': {
        'kicker': 'Help centre', 'title': 'Frequently asked questions.',
        'intro': 'Answers to common questions about shopping, delivery, returns and grooming.',
        'sections': [
            ('Do you deliver?', 'Yes. Contact our team with your location and order details to confirm delivery availability and charges.'),
            ('How can I book grooming?', 'Use our online Grooming page to select your pet, package, preferred date and time.'),
            ('Which payment methods do you accept?', 'Available payment methods are shown during checkout and at our stores.'),
            ('Can I return an item?', 'Eligible defective or incorrect items may be returned under our Returns policy.'),
        ],
    },
    'grooming-policy': {
        'kicker': 'Grooming studio', 'title': 'Grooming policy.',
        'intro': 'These guidelines keep every pet safe, comfortable and cared for throughout their appointment.',
        'sections': [
            ('Before your appointment', 'Please disclose medical conditions, allergies and behavioural concerns. Arrive approximately ten minutes early for check-in.'),
            ('During grooming', 'Services may be adjusted when coat condition or behaviour requires additional handling, detangling or another safety measure.'),
            ('Pickup', 'We will contact you when grooming is complete. Please collect your pet within one hour to avoid late-pickup charges.'),
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
            ('Payments', 'Payment must be completed using an accepted method. Prices are displayed in Tanzanian shillings unless stated otherwise.'),
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
            ('Dar es Salaam delivery', 'Delivery timing and charges depend on your location, order size and product availability.'),
            ('Before dispatch', 'Our team may contact you to confirm your address, phone number, items and payment details.'),
            ('Need an update?', 'Contact us by phone or WhatsApp with your order reference and we will help you track its progress.'),
        ],
    },
}


class StephansWebsitePages(http.Controller):
    @http.route(['/about', '/contact', '/stores', '/allbrands', '/faq', '/faqs', '/grooming-policy', '/return-policy', '/terms', '/blog', '/delivery'], type='http', auth='public', website=True)
    def content_page(self, **kw):
        key = request.httprequest.path.strip('/') or 'about'
        if key == 'faqs': key = 'faq'
        return request.render('stephans_website_theme.content_page', {'page': PAGES[key], 'page_key': key})

    @http.route(['/shop/dogs', '/shop/cats', '/shop/small-pets', '/shop/pet-food', '/shop/accessories'], type='http', auth='public', website=True)
    def shop_alias(self, **kw):
        term = request.httprequest.path.rsplit('/', 1)[-1].replace('-', ' ')
        return request.redirect('/shop?search=' + term)

    @http.route('/cart', type='http', auth='public', website=True)
    def cart_alias(self, **kw):
        return request.redirect('/shop/cart')
