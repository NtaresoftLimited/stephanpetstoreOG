{
    "name": "SKY Dashboard",
    "version": "20.0.1.0.1",
    "category": "Productivity/Dashboard",
    "summary": "Minimal business overview for Stephans Pet Store",
    "author": "Stephans Pet Store",
    "website": "https://stephans-pet-store.com",
    "license": "LGPL-3",
    "depends": ["sale_management", "stock", "point_of_sale"],
    "data": [
        "security/sky_stock_security.xml",
        "data/sky_stock_cron.xml",
        "reports/sky_stock_report.xml",
        "wizard/sky_stock_generate_wizard_views.xml",
        "views/sky_daily_stock_views.xml",
        "views/sky_dashboard_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "sky_dashboard/static/src/js/sky_dashboard.js",
            "sky_dashboard/static/src/xml/sky_dashboard.xml",
            "sky_dashboard/static/src/scss/sky_dashboard.scss",
        ],
    },
    "application": True,
    "installable": True,
    "auto_install": False,
    "post_init_hook": "post_init_hook",
}
