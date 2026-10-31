{
    "name": "Stephan's Pet Store Website Theme",
    "version": "20.0.1.1.2",
    "category": "Theme/eCommerce",
    "summary": "Isolated Stephan's Pet Store website preview",
    "author": "Stephan's Pet Store",
    "website": "https://stephanspetstore.co.tz",
    "depends": ["website", "website_sale", "grooming"],
    "data": [
        "views/header.xml",
        "views/footer.xml",
        "views/layout.xml",
        "views/homepage.xml",
        "views/grooming.xml",
        "views/pages.xml",
        "data/pages.xml",
        "data/products.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "stephans_website_theme/static/src/js/header.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
