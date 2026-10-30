from odoo import models, fields, api

class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    pos_payment_method_id = fields.Many2one(
        'pos.payment.method',
        string='Payment Method (POS)',
        domain="[('journal_id', '!=', False), ('company_id', '=', company_id)]",
        help="Select a Point of Sale payment method to auto-fill the accounting journal."
    )

    @api.onchange('pos_payment_method_id')
    def _onchange_pos_payment_method_id(self):
        for wizard in self:
            if wizard.pos_payment_method_id and wizard.pos_payment_method_id.journal_id:
                wizard.journal_id = wizard.pos_payment_method_id.journal_id
