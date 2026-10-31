{
    "name": "Stephans Odoo 20 Browser Compatibility",
    "version": "20.0.1.0.1",
    "category": "Technical",
    "summary": "Safe browser API fallbacks for the isolated Odoo 20 preview",
    "author": "Stephans Pet Store",
    "license": "LGPL-3",
    "depends": ["web"],
    "assets": {
        "web.assets_web": [
            ("prepend", "odoo20_browser_compat/static/src/js/browser_api_fallbacks.js"),
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
