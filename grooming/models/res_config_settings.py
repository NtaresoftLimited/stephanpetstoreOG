# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    grooming_detangling_fee = fields.Float(
        string="Detangling Fee",
        config_parameter='grooming.detangling_fee',
        default=30000.0,
        help="Fee charged when detangling is required."
    )
    grooming_handling_fee = fields.Float(
        string="Handling Fee",
        config_parameter='grooming.handling_fee',
        default=20000.0,
        help="Fee charged for difficult pets handling."
    )
    grooming_late_pickup_fee = fields.Float(
        string="Late Pickup Fee (per Hour)",
        config_parameter='grooming.late_pickup_fee',
        default=10000.0,
        help="Hourly fee for late pickups."
    )
