from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    ai_provider = fields.Selection([
        ('openai', 'OpenAI (ChatGPT)'),
        ('gemini', 'Google Gemini')
    ], string="Active AI Engine",
       default='gemini',
       config_parameter='stephans_product_ai_enrich.ai_provider',
       help="Select which AI engine to use for generating product catalogue data."
    )

    # OpenAI Settings
    openai_api_key = fields.Char(
        string="OpenAI API Key",
        help="API Key for ChatGPT (e.g. sk-...)",
        config_parameter='stephans_product_ai_enrich.openai_api_key'
    )
    openai_model = fields.Char(
        string="OpenAI Model",
        default="gpt-4o",
        help="Model ID to use for product enrichment (e.g. gpt-4o or gpt-4o-mini)",
        config_parameter='stephans_product_ai_enrich.openai_model'
    )

    # Google Gemini Settings
    gemini_api_key = fields.Char(
        string="Gemini API Key",
        help="Google Gemini API Key (e.g. AIzaSy...)",
        config_parameter='stephans_product_ai_enrich.gemini_api_key'
    )
    gemini_model = fields.Char(
        string="Gemini Model",
        default="gemini-3.6-flash",
        help="Model ID to use for product enrichment (e.g. gemini-3.6-flash, gemini-3.5-flash-lite, or gemini-3.8-flash)",
        config_parameter='stephans_product_ai_enrich.gemini_model'
    )
