# -*- coding: utf-8 -*-
from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    crm_q2_inactivity_days = fields.Integer(
        string='Q2 Slipping Threshold (Days)',
        default=30,
        config_parameter='stephans_corporate_crm.q2_days',
        help="Number of days without sales or grooming before an account shifts from Q1 to Q2 (Default: 30 days / 1 month)."
    )
    crm_q3_inactivity_days = fields.Integer(
        string='Q3 Dormant Threshold (Days)',
        default=60,
        config_parameter='stephans_corporate_crm.q3_days',
        help="Number of days without sales or grooming before an account shifts to Q3 (Default: 60 days / 2 months)."
    )
    crm_q4_inactivity_days = fields.Integer(
        string='Q4 Churned Threshold (Days)',
        default=90,
        config_parameter='stephans_corporate_crm.q4_days',
        help="Number of days without sales or grooming before an account is marked as Q4 Churned (Default: 90 days / 3 months)."
    )
    crm_auto_create_activity = fields.Boolean(
        string='Auto-Schedule Activity for KAM on Demotion',
        default=True,
        config_parameter='stephans_corporate_crm.auto_create_activity',
        help="Automatically schedule a call or follow-up activity for the Key Account Manager when an account slips into Q2, Q3, or Q4."
    )
    crm_auto_whatsapp_prompt = fields.Boolean(
        string='Enable One-Click WhatsApp Re-engagement',
        default=True,
        config_parameter='stephans_corporate_crm.auto_whatsapp_prompt',
        help="Provide one-click WhatsApp action buttons on customer cards and form views."
    )
