# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    pos_payment_method_id = fields.Many2one(
        'pos.payment.method',
        string="Payment Method",
        compute='_compute_pos_payment_method_id',
        store=True,
        readonly=False,
        domain="[('journal_id', '!=', False), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",
        help="Select the payment method (CRDB Bank, NMB Bank, M-Pesa, Tigo Pesa, or Cash)."
    )
    reference_number = fields.Char(
        string="Ref Number",
        help="Enter the Bank or Mobile Money Reference Number (e.g. M-Pesa, Tigo Pesa, CRDB, or NMB Ref)."
    )
    ref_number_required = fields.Boolean(
        compute='_compute_ref_number_required',
        string="Reference Number Required"
    )

    @api.depends('journal_id', 'company_id')
    def _compute_pos_payment_method_id(self):
        PosMethod = self.env['pos.payment.method'].sudo()
        for wizard in self:
            if wizard.pos_payment_method_id and wizard.pos_payment_method_id.journal_id == wizard.journal_id:
                continue
            domain = [
                ('journal_id', '=', wizard.journal_id.id),
                '|', ('company_id', '=', False), ('company_id', '=', wizard.company_id.id),
            ]
            method = PosMethod.search(domain, limit=1)
            if not method:
                fallback_domain = [
                    ('journal_id', '!=', False),
                    '|', ('company_id', '=', False), ('company_id', '=', wizard.company_id.id),
                ]
                method = PosMethod.search(fallback_domain, limit=1)
            wizard.pos_payment_method_id = method

    @api.onchange('pos_payment_method_id')
    def _onchange_pos_payment_method_id(self):
        for wizard in self:
            if wizard.pos_payment_method_id and wizard.pos_payment_method_id.journal_id:
                wizard.journal_id = wizard.pos_payment_method_id.journal_id

    @api.depends('journal_id', 'pos_payment_method_id')
    def _compute_ref_number_required(self):
        for wizard in self:
            if wizard.pos_payment_method_id:
                wizard.ref_number_required = (wizard.pos_payment_method_id.type == 'bank')
            else:
                journal = wizard.journal_id
                wizard.ref_number_required = bool(journal and journal.type == 'bank')

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)
        ref = (self.reference_number or '').strip()
        if self.ref_number_required and not ref:
            method_label = self.pos_payment_method_id.name or self.journal_id.name or _('Bank / Mobile Money')
            raise UserError(
                _("A Reference Number is required for %s. Please enter the transaction reference before validating this payment.")
                % method_label
            )
        if ref:
            vals['memo'] = ref
        if self.pos_payment_method_id:
            vals['pos_payment_method_id'] = self.pos_payment_method_id.id
        return vals

    def _create_payment_vals_from_batch(self, batch_result):
        vals = super()._create_payment_vals_from_batch(batch_result)
        ref = (self.reference_number or '').strip()
        if self.ref_number_required and not ref:
            method_label = self.pos_payment_method_id.name or self.journal_id.name or _('Bank / Mobile Money')
            raise UserError(
                _("A Reference Number is required for %s. Please enter the transaction reference before validating this payment.")
                % method_label
            )
        if ref:
            vals['memo'] = ref
        if self.pos_payment_method_id:
            vals['pos_payment_method_id'] = self.pos_payment_method_id.id
        return vals
