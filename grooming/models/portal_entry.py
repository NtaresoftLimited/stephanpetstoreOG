# -*- coding: utf-8 -*-
from odoo import models


class PortalEntry(models.Model):
    _inherit = "portal.entry"

    def _filter_visible_portal_cards(self):
        visible_entries = super()._filter_visible_portal_cards()
        # Ensure pet grooming, my pets, and in-store purchases are always visible cards for customers
        stephans_cards = self.filtered(lambda e: e.url in ('/my/grooming', '/my/pets', '/my/pos_orders'))
        return visible_entries | stephans_cards
