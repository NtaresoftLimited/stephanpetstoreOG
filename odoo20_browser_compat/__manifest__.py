{
    "name": "Stephans Odoo 20 Browser Compatibility",
    "version": "20.0.1.0.3",
    "category": "Technical",
    "summary": "Safe browser API fallbacks for the isolated Odoo 20 preview",
    "author": "Stephans Pet Store",
    "license": "LGPL-3",
    "depends": ["web", "mail"],
    "assets": {
        "web.assets_web": [
            "odoo20_browser_compat/static/src/js/browser_api_fallbacks.js",
            "odoo20_browser_compat/static/src/js/ptt_extension_guard.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
}
