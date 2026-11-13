# -*- coding: utf-8 -*-
"""The portal cards were first loaded with noupdate="1", so later upgrades never refreshed
their names/icons. Clear the flag so data/portal_entry_data.xml (now noupdate="0") applies."""


def migrate(cr, version):
    cr.execute(
        """
        UPDATE ir_model_data
           SET noupdate = false
         WHERE module = 'grooming'
           AND model = 'portal.entry'
           AND name IN ('portal_entry_grooming', 'portal_entry_pets', 'portal_entry_pos_orders')
        """
    )
