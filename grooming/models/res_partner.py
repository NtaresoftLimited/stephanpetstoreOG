# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_replenishment_vendor = fields.Boolean(
        string='Is Replenishment Vendor',
        default=False,
        help='Indicates whether this partner is the internal default replenishment vendor, hidden from POS cashiers.'
    )

    @api.model
    def _load_pos_data_domain(self, data):
        domain = super()._load_pos_data_domain(data)
        return domain + [('is_replenishment_vendor', '=', False)]

    @api.model
    def _search(self, domain, offset=0, limit=None, order=None):
        user = self.env.user
        if not user._is_superuser() and not user.has_group('stock.group_stock_manager') and not user.has_group('account.group_account_invoice'):
            domain = (domain or []) + [('is_replenishment_vendor', '=', False)]
        return super()._search(domain, offset=offset, limit=limit, order=order)

    @api.model
    def search_read(self, domain=None, fields=None, offset=0, limit=None, order=None, **kwargs):
        user = self.env.user
        if not user._is_superuser() and not user.has_group('stock.group_stock_manager') and not user.has_group('account.group_account_invoice'):
            domain = (domain or []) + [('is_replenishment_vendor', '=', False)]
        return super().search_read(domain=domain, fields=fields, offset=offset, limit=limit, order=order, **kwargs)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        user = self.env.user
        if not user._is_superuser() and not user.has_group('stock.group_stock_manager') and not user.has_group('account.group_account_invoice'):
            args = (args or []) + [('is_replenishment_vendor', '=', False)]
        return super().name_search(name=name, args=args, operator=operator, limit=limit)
