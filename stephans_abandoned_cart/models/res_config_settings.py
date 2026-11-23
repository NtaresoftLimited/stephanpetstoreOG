# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    abandoned_cart_enabled = fields.Boolean(
        string="Enable Abandoned Cart Recovery",
        config_parameter="stephans_abandoned_cart.enabled",
        default=True,
        help="Automatically detect abandoned carts and send recovery email reminders.",
    )
    abandoned_cart_delay_minutes = fields.Integer(
        string="Inactivity Threshold (Minutes)",
        config_parameter="stephans_abandoned_cart.delay_minutes",
        default=30,
        help="Number of minutes without activity before a shopping cart is considered abandoned.",
    )
    abandoned_cart_reminder_delay_minutes = fields.Integer(
        string="First Reminder Delay (Minutes)",
        config_parameter="stephans_abandoned_cart.reminder_delay_minutes",
        default=15,
        help="Number of minutes after cart is marked abandoned before sending the first reminder email.",
    )
    abandoned_cart_max_reminders = fields.Integer(
        string="Maximum Reminders Per Cart",
        config_parameter="stephans_abandoned_cart.max_reminders",
        default=2,
        help="Maximum number of reminder emails to send for a single abandoned cart.",
    )
    abandoned_cart_template_id = fields.Many2one(
        "mail.template",
        string="Default Reminder Email Template",
        domain="[('model', '=', 'sale.order')]",
        config_parameter="stephans_abandoned_cart.template_id",
        help="The email template used to send abandoned cart reminders.",
    )
