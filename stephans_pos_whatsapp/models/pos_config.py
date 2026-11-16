from odoo import fields, models


class PosConfig(models.Model):
    _inherit = "pos.config"

    whatsapp_receipt = fields.Boolean(
        string="WhatsApp Receipts",
        default=True,
        help="Show a WhatsApp button in the Send Receipt popup to send the receipt image "
             "to the customer's WhatsApp (WaSender account in stephans_whatsapp.api_key).",
    )


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    pos_whatsapp_receipt = fields.Boolean(related="pos_config_id.whatsapp_receipt", readonly=False)
