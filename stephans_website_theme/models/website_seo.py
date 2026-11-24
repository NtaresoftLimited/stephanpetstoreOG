import logging
from odoo import models
from odoo.http import request

_logger = logging.getLogger(__name__)


class IrHttp(models.AbstractModel):
    _inherit = 'ir.http'

    @classmethod
    def _dispatch(cls, endpoint):
        req = request.httprequest
        host = req.host.split(':')[0]
        # Permanent 301 redirect non-www to canonical www domain
        if host == 'stephanspetstore.co.tz':
            query = ('?' + req.query_string.decode('utf-8')) if req.query_string else ''
            target_url = 'https://www.stephanspetstore.co.tz' + req.path + query
            return request.redirect(target_url, code=301, local=False)
        return super()._dispatch(endpoint)


class WebsiteSeoMetadata(models.AbstractModel):
    _inherit = 'website.seo.metadata'

    def get_website_meta(self):
        """Suppress automatic Odoo logo opengraph tags so the theme controls singular og tags."""
        res = super().get_website_meta()
        res['opengraph_meta'] = {}
        res['twitter_meta'] = {}
        return res
