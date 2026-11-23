{
    'name': "Stephan's AI Product Catalog & Media Enricher",
    'version': '20.0.1.2.0',
    'summary': "Regenerate rich catalog descriptions, attributes, EAN barcodes, and watermark-free pictures with strict image quality gate & media review queue",
    'category': 'Sales/Products',
    'author': "Stephan's Pet Store",
    'website': "https://stephanspetstore.co.tz",
    'depends': ['product', 'website_sale'],
    'data': [
        'security/ir.access.csv',
        'data/ir_cron_data.xml',
        'views/res_config_settings_views.xml',
        'views/product_template_views.xml',
        'views/product_image_review_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
