from odoo import http
from odoo.http import request


class StephansWebsiteHome(http.Controller):
    @http.route("/", type="http", auth="public", website=True, sitemap=True)
    def homepage(self, **kwargs):
        return request.render("stephans_website_theme.stephans_preview_page")
