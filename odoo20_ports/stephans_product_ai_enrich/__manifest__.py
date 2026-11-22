{
    'name': "Stephan's AI Product Catalog & Media Enricher",
    'version': '20.0.1.1.0',
    'summary': "Regenerate rich catalog descriptions, attributes, EAN barcodes, and watermark-free pictures using Gemini/ChatGPT and official brand catalog seeds",
    'category': 'Sales/Products',
    'author': "Stephan's Pet Store",
    'website': "https://stephanspetstore.co.tz",
    'depends': ['product', 'website_sale'],
    'data': [
        'data/ir_cron_data.xml',
        'views/res_config_settings_views.xml',
        'views/product_template_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
