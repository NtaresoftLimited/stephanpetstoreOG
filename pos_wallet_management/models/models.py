# -*- coding: utf-8 -*-
#################################################################################
#
#   Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>)
#   See LICENSE file for full copyright and licensing details.
#   License URL : <https://store.webkul.com/license.html/>
#
#################################################################################

from odoo import api, fields, models, _
import functools
import json
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PosWallet(models.Model):
    _name = 'pos.wallet'
    _inherit = ['pos.load.mixin']
    _order = "id desc"
    _description = "Sky Wallet"

    name = fields.Char(string="Name", default="New", readonly=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string="Partner", required=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="Currency",
        related='company_id.currency_id',
        store=True,
        readonly=True,
    )
    created_by = fields.Many2one(comodel_name='res.users', string="Created By", default=lambda self: self.env.user)
    create_date = fields.Datetime('Creation Date', default=fields.Datetime.now)
    amount = fields.Monetary(
        string="Balance",
        currency_field='currency_id',
        compute='_total_credit_points_available',
    )
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'), ('confirm', 'Confirm'), ('cancel', 'Cancel')],
        default='draft',
        required=True,
    )
    pos_wallet_trans_id = fields.One2many(
        comodel_name='pos.wallet.transaction',
        inverse_name='wallet_id',
        string="Sky Wallet Transactions",
        readonly=True,
    )
    reason = fields.Text(string="Sky Wallet Cancellation Reason", readonly=True)
    nfcid = fields.Char(string="NFC Code", help="NFC code used for Sky Wallet customer identification.", copy=False)

    @api.constrains('nfcid', 'state')
    def _check_unique_nfcid(self):
        for record in self:
            if record.nfcid and record.state != 'cancel':
                existing = self.search([
                    ('nfcid', '=', record.nfcid),
                    ('id', '!=', record.id),
                    ('state', '!=', 'cancel')
                ], limit=1)
                if existing:
                    raise ValidationError(_("The NFC Code must be unique for active wallets."))

    @api.constrains('partner_id', 'state')
    def validate_partner(self):
        for record in self:
            if record.partner_id and record.state == 'confirm':
                existing = self.search([
                    ('state', '=', 'confirm'),
                    ('partner_id', '=', record.partner_id.id),
                    ('id', '!=', record.id),
                ], limit=1)
                if existing:
                    raise ValidationError(_("Customer '%s' already has an active wallet (%s). Multiple active wallets are not permitted.", record.partner_id.name, existing.name))

    @api.model
    def _load_pos_data_fields(self, config_id):
        return [
            'id', 'name', 'partner_id', 'company_id', 'currency_id',
            'create_date', 'amount', 'state', 'pos_wallet_trans_id', 'reason', 'nfcid'
        ]

    @api.model
    def _load_pos_data_domain(self, data):
        return [('state', 'in', ['confirm'])]

    def _total_credit_points_available(self):
        for record in self:
            transactions = record.pos_wallet_trans_id.filtered(lambda t: t.state == 'confirm')
            credits = sum(transactions.filtered(lambda t: t.payment_type in ('CREDIT', 'REFUND')).mapped('amount'))
            debits = sum(transactions.filtered(lambda t: t.payment_type == 'DEBIT').mapped('amount'))
            balance = credits - debits
            currency = record.currency_id or record.partner_id.property_product_pricelist.currency_id or self.env.company.currency_id
            record.amount = currency.round(balance) if currency else round(balance, 2)

    @api.model
    def create_wallet_by_rpc(self, data):
        """Allows POS cashier to securely initialize and confirm a wallet via server sudo."""
        partner_id = data.get('partner_id')
        if not partner_id:
            raise UserError(_("Customer is required to create a wallet."))

        existing = self.sudo().search([('partner_id', '=', partner_id), ('state', '=', 'confirm')], limit=1)
        if existing:
            return {
                'id': existing.id,
                'name': existing.name,
                'amount': existing.amount,
            }

        vals = dict(data)
        if not vals.get('company_id'):
            vals['company_id'] = self.env.company.id
        wallet = self.sudo().create(vals)
        wallet.sudo().confirm_wallet()
        return {
            'amount': 0.0,
            'id': wallet.id,
            'name': wallet.name,
        }

    def confirm_wallet(self):
        for record in self:
            existing = self.search([
                ('state', '=', 'confirm'),
                ('partner_id', '=', record.partner_id.id),
                ('id', '!=', record.id),
            ], limit=1)
            if existing:
                raise ValidationError(_("Customer '%s' already has an active wallet (%s).", record.partner_id.name, existing.name))
            if record.name == 'New':
                record.name = self.env['ir.sequence'].next_by_code('pos.wallet') or _("New")
            record.partner_id.sudo().wallet_id = record.id
            record.state = 'confirm'

    def action_cancel(self):
        for wallet in self:
            if wallet.amount > 0:
                currency_sym = wallet.currency_id.symbol or wallet.currency_id.name or ''
                raise UserError(
                    _("Cannot cancel wallet '%(wallet)s' with an active balance of %(bal)s %(curr)s.\n"
                      "Reconcile or refund the remaining balance before cancellation.",
                      wallet=wallet.name,
                      bal=wallet.amount,
                      curr=currency_sym)
                )
            wallet.state = 'cancel'
            wallet.partner_id.sudo().wallet_id = False

    def unlink(self):
        for obj in self:
            if obj.pos_wallet_trans_id:
                raise ValidationError(_("Cannot delete wallet '%s' because financial transaction history exists.") % obj.name)
            if obj.state in ['confirm', 'cancel']:
                raise ValidationError(_("Cannot delete confirmed or cancelled wallet '%s'.") % obj.name)
        return super(PosWallet, self).unlink()

    def debit_wallet(self, amount, pos_order=None, user_id=None, reason=None, check_balance=True):
        """
        Atomically debits the wallet using SELECT ... FOR UPDATE row-level locking.
        Prevents concurrent overspending across multiple POS terminals.
        """
        self.ensure_one()
        if amount <= 0:
            raise ValidationError(_("Debit amount must be strictly greater than zero."))

        # Explicit row-level lock on the pos_wallet record
        self.env.cr.execute("SELECT id, state FROM pos_wallet WHERE id = %s FOR UPDATE", [self.id])
        self.invalidate_recordset(['amount', 'pos_wallet_trans_id'])

        if self.state != 'confirm':
            raise UserError(_("Wallet '%s' is not active.", self.name))

        currency = self.currency_id or self.env.company.currency_id
        rounded_amount = currency.round(amount) if currency else round(amount, 2)

        if check_balance and self.amount < rounded_amount:
            raise UserError(
                _("Insufficient Sky Wallet balance for customer %(partner)s.\n"
                  "Available Balance: %(balance)s\n"
                  "Requested Debit: %(amount)s",
                  partner=self.partner_id.name,
                  balance=self.amount,
                  amount=rounded_amount)
            )

        vals = {
            'wallet_id': self.id,
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'amount': rounded_amount,
            'payment_type': 'DEBIT',
            'trans_reason': reason or _('Sky Wallet POS Payment'),
            'pos_order_id': pos_order.id if pos_order else False,
            'created_by': user_id or self.env.uid,
            'name': pos_order.name if pos_order else _('Sky Wallet Debit'),
        }
        return self.env['pos.wallet.transaction'].sudo().create(vals)

    def credit_wallet(self, amount, pos_order=None, user_id=None, reason=None):
        """
        Atomically credits the wallet using SELECT ... FOR UPDATE row-level locking.
        """
        self.ensure_one()
        if amount <= 0:
            raise ValidationError(_("Recharge amount must be strictly greater than zero."))

        # Explicit row-level lock on the pos_wallet record
        self.env.cr.execute("SELECT id, state FROM pos_wallet WHERE id = %s FOR UPDATE", [self.id])
        self.invalidate_recordset(['amount', 'pos_wallet_trans_id'])

        if self.state != 'confirm':
            raise UserError(_("Wallet '%s' is not active.", self.name))

        currency = self.currency_id or self.env.company.currency_id
        rounded_amount = currency.round(amount) if currency else round(amount, 2)

        vals = {
            'wallet_id': self.id,
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'amount': rounded_amount,
            'payment_type': 'CREDIT',
            'trans_reason': reason or _('Sky Wallet Recharge'),
            'pos_order_id': pos_order.id if pos_order else False,
            'created_by': user_id or self.env.uid,
            'name': pos_order.name if pos_order else _('Sky Wallet Recharge'),
        }
        return self.env['pos.wallet.transaction'].sudo().create(vals)

    def refund_wallet(self, amount, original_trans=None, pos_order=None, user_id=None, reason=None):
        """
        Atomically refunds to the wallet with original transaction audit linkage.
        """
        self.ensure_one()
        if amount <= 0:
            raise ValidationError(_("Refund amount must be strictly greater than zero."))

        self.env.cr.execute("SELECT id, state FROM pos_wallet WHERE id = %s FOR UPDATE", [self.id])
        self.invalidate_recordset(['amount', 'pos_wallet_trans_id'])

        if self.state != 'confirm':
            raise UserError(_("Wallet '%s' is not active.", self.name))

        currency = self.currency_id or self.env.company.currency_id
        rounded_amount = currency.round(amount) if currency else round(amount, 2)

        if original_trans:
            if original_trans.payment_type != 'DEBIT':
                raise UserError(_("Refund can only be applied against a DEBIT transaction."))
            already_refunded = sum(original_trans.refund_transaction_ids.mapped('amount'))
            if rounded_amount + already_refunded > original_trans.amount:
                max_allowed = original_trans.amount - already_refunded
                raise UserError(
                    _("Refund amount %(amount)s exceeds remaining refundable balance %(max)s on transaction %(tx)s.",
                      amount=rounded_amount, max=max_allowed, tx=original_trans.name)
                )

        vals = {
            'wallet_id': self.id,
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id,
            'amount': rounded_amount,
            'payment_type': 'REFUND',
            'original_transaction_id': original_trans.id if original_trans else False,
            'trans_reason': reason or _('Sky Wallet POS Refund'),
            'pos_order_id': pos_order.id if pos_order else False,
            'created_by': user_id or self.env.uid,
            'name': pos_order.name if pos_order else _('Sky Wallet Refund'),
        }
        return self.env['pos.wallet.transaction'].sudo().create(vals)

    @api.model
    def create_demo_data(self):
        pos_configs = self.env['pos.config'].search([])
        company = pos_configs[0].company_id if pos_configs else self.env.company
        ctx = dict(self.env.context, company_id=company.id)
        req_pos_payment_method = self.env['pos.payment.method'].with_context(ctx).search(
            [('wallet_method', '=', True)], limit=1
        )
        req_journal = self.env['account.journal'].with_context(ctx).search(
            [('name', 'in', ['Sky Wallet Journal', 'WkPosCashWallet'])], limit=1
        )

        if len(req_journal) < 1:
            req_journal = self.env['account.journal'].with_context(ctx).create({
                'name': 'Sky Wallet Journal',
                'code': 'SKYWL',
                'type': 'cash',
                'sequence': 100,
            })
            req_journal = [req_journal]
        if len(req_pos_payment_method) < 1 and len(req_journal) >= 1:
            method_vals = {
                'name': 'Sky Wallet',
                'wallet_method': True,
                'journal_id': req_journal[0].id,
            }
            if 'type' in self.env['pos.payment.method']._fields:
                method_vals['type'] = 'cash'
            if 'is_cash_count' in self.env['pos.payment.method']._fields:
                method_vals['is_cash_count'] = True
            req_pos_payment_method = self.env['pos.payment.method'].with_context(ctx).create(method_vals)
            req_pos_payment_method = [req_pos_payment_method]
        if len(req_pos_payment_method) >= 1 and len(req_journal) >= 1 and pos_configs:
            try:
                pos_configs[0].with_context(ctx).write({
                    'payment_method_ids': [(4, req_pos_payment_method[0].id)]
                })
            except Exception as e:
                _logger.warning("Could not auto-attach Sky Wallet to the active POS configuration: %s", e)

    def action_register_payment(self, ctx=None):
        context = {
            'active_model': 'pos.wallet',
            'active_ids': self.ids,
            'default_memo': 'RC@' + self.name
        }
        if ctx:
            context.update(ctx)
        return {
            'name': _('Recharge'),
            'res_model': 'wallet.recharge',
            'view_mode': 'form',
            'views': [[False, 'form']],
            'context': context,
            'target': 'new',
            'type': 'ir.actions.act_window',
        }


class ResPartner(models.Model):
    _inherit = 'res.partner'

    wallet_id = fields.Many2one(comodel_name="pos.wallet", string="Sky Wallet")
    wallet_credits = fields.Monetary(string="Sky Wallet Balance", related='wallet_id.amount', currency_field='currency_id')
    wallet_counts = fields.Integer(compute='_compute_wallet_counts', string="Sky Wallets")

    def _load_pos_data_fields(self, config_id):
        data = super()._load_pos_data_fields(config_id)
        data += ["wallet_id", "wallet_credits", "wallet_counts"]
        return data

    def _compute_wallet_counts(self):
        wallet_data = self.env['pos.wallet'].read_group(
            [('partner_id', 'in', self.ids), ('state', '=', 'confirm')],
            ['partner_id'],
            ['partner_id']
        )
        mapped_data = dict([(wallet['partner_id'][0], wallet['partner_id_count']) for wallet in wallet_data])
        for partner in self:
            partner.wallet_counts = mapped_data.get(partner.id, 0)

    def action_customer_wallet(self):
        context = self._context
        Wallet = self.env['pos.wallet'].search(
            [('partner_id', 'in', self.ids), ('state', '=', 'confirm')]
        )
        if not Wallet:
            tree_view_action = self.env.ref(
                'pos_wallet_management.pos_wallet_action_window').read()[0]
            tree_view_action['context'] = {
                'search_default_partner_id': context.get('active_id', False),
                'partner_id': context.get('active_id', False)
            }
            return tree_view_action
        return {
            'name': _('Sky Wallet'),
            'view_mode': 'form',
            'view_id': self.env.ref('pos_wallet_management.pos_wallet_form').id,
            'res_model': 'pos.wallet',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': Wallet and Wallet.ids[0] or False,
        }


class PosWalletTranscation(models.Model):
    _name = 'pos.wallet.transaction'
    _inherit = ['pos.load.mixin']
    _order = "id desc"
    _description = "Sky Wallet Transaction"

    name = fields.Char(string="Name")
    wallet_id = fields.Many2one(comodel_name="pos.wallet", string="Related Sky Wallet", readonly=True, required=True, ondelete='restrict')
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="Currency",
        related='company_id.currency_id',
        store=True,
        readonly=True,
    )
    partner_id = fields.Many2one(comodel_name='res.partner', string="Partner", required=True)
    created_by = fields.Many2one(comodel_name='res.users', string="Salesman", default=lambda self: self.env.user)
    amount = fields.Monetary(string="Amount", currency_field='currency_id', required=True)
    pos_order_id = fields.Many2one(string="POS Order", comodel_name="pos.order", ondelete='set null')
    payment_type = fields.Selection(
        string='Type',
        selection=[('CREDIT', 'CREDIT'), ('DEBIT', 'DEBIT'), ('REFUND', 'REFUND')],
        default='CREDIT',
        required=True,
    )
    state = fields.Selection(string='State', related="wallet_id.state", store=True)
    create_date = fields.Datetime('Date', default=fields.Datetime.now, readonly=True)
    trans_reason = fields.Text(string='Transaction Reason', required=True)
    original_transaction_id = fields.Many2one(
        comodel_name='pos.wallet.transaction',
        string='Original Transaction',
        ondelete='restrict',
        help="Linked debit transaction when this record is a refund.",
    )
    refund_transaction_ids = fields.One2many(
        comodel_name='pos.wallet.transaction',
        inverse_name='original_transaction_id',
        string='Refund Transactions',
    )

    @api.constrains('amount')
    def _check_amount_positive(self):
        for rec in self:
            if rec.amount <= 0:
                raise ValidationError(_("Transaction amount must be strictly greater than zero."))

    @api.model
    def _load_pos_data_fields(self, config_id):
        return [
            "name", "wallet_id", "company_id", "currency_id", "partner_id",
            "created_by", "amount", "pos_order_id", "payment_type", "state",
            "trans_reason", "create_date", "original_transaction_id"
        ]

    @api.model
    def _load_pos_data_domain(self, data):
        return [('wallet_id.state', 'in', ['confirm'])]

    def write(self, vals):
        # Strict financial immutability
        immutable_fields = {'amount', 'partner_id', 'wallet_id', 'payment_type', 'pos_order_id', 'company_id', 'original_transaction_id'}
        if any(f in vals for f in immutable_fields):
            raise UserError(_("Financial transactions are immutable. Modifications to financial ledger fields are prohibited."))
        return super(PosWalletTranscation, self).write(vals)

    def unlink(self):
        raise UserError(_("Financial transactions cannot be deleted. Ledger records are permanent for audit integrity."))


class PosOrder(models.Model):
    _inherit = "pos.order"

    wallet_recharge_data = fields.Text("wallet recharge data")

    def _create_sky_wallet_transaction_once(self, values):
        """Keep POS retries from duplicating a Sky Wallet movement."""
        Transaction = self.env['pos.wallet.transaction'].sudo()
        domain = [
            ('pos_order_id', '=', values.get('pos_order_id')),
            ('wallet_id', '=', values.get('wallet_id')),
            ('payment_type', '=', values.get('payment_type')),
            ('amount', '=', values.get('amount')),
        ]
        transaction = Transaction.search(domain, limit=1)
        if transaction:
            return transaction
        return Transaction.create(values)

    @api.model
    def sync_from_ui(self, orders):
        order_ids = super(PosOrder, self).sync_from_ui(orders)
        wallet_method = self.env['pos.payment.method'].search([('wallet_method', '=', True)], limit=1)

        if wallet_method:
            for index, order in enumerate(orders):
                order_data = order
                pos_order = self.env['pos.order'].search(
                    [('pos_reference', '=', order_data.get('name'))], limit=1
                )
                if order_data and order_data.get('partner_id') and pos_order:
                    currency = pos_order.pricelist_id.currency_id

                    wallet_trans_data_temp = order_data.get('wallet_recharge_data')
                    wallet_trans_data = False
                    if wallet_trans_data_temp:
                        wallet_trans_data = json.loads(wallet_trans_data_temp)

                    # Wallet Recharge via POS order
                    if wallet_trans_data and wallet_trans_data.get('wallet_product_id'):
                        wallet_id = self.env['pos.wallet'].search(
                            [('id', '=', wallet_trans_data.get('wallet_id')), ('state', '=', 'confirm')],
                            limit=1,
                        )
                        if wallet_id:
                            subtotal_list = pos_order.lines.filtered(
                                lambda line: line.product_id.id == wallet_trans_data.get('wallet_product_id')
                            ).mapped('price_subtotal_incl')
                            if len(subtotal_list):
                                sub_total = functools.reduce(lambda x, y: x + y, subtotal_list)
                                recharge_amount = currency.round(sub_total)
                                existing_tx = self.env['pos.wallet.transaction'].sudo().search([
                                    ('pos_order_id', '=', pos_order.id),
                                    ('wallet_id', '=', wallet_id.id),
                                    ('payment_type', '=', 'CREDIT'),
                                ], limit=1)
                                if not existing_tx:
                                    wallet_id.credit_wallet(
                                        amount=recharge_amount,
                                        pos_order=pos_order,
                                        user_id=order_data.get('user_id'),
                                        reason=_('Sky Wallet POS Recharge'),
                                    )
                    else:
                        # Wallet Payment / Refund via POS order
                        wallet_id = self.env['pos.wallet'].search(
                            [('partner_id', '=', order_data.get('partner_id')), ('state', '=', 'confirm')],
                            limit=1,
                        )
                        if wallet_id and pos_order:
                            for payment in order_data.get('payment_ids', []):
                                payment_values = (
                                    payment[2]
                                    if isinstance(payment, (list, tuple)) and len(payment) > 2
                                    else payment
                                )
                                if not isinstance(payment_values, dict):
                                    continue
                                if payment_values.get('payment_method_id') == wallet_method.id:
                                    raw_amount = payment_values.get('amount', 0.0)
                                    if raw_amount > 0:
                                        # Debit
                                        existing_tx = self.env['pos.wallet.transaction'].sudo().search([
                                            ('pos_order_id', '=', pos_order.id),
                                            ('wallet_id', '=', wallet_id.id),
                                            ('payment_type', '=', 'DEBIT'),
                                        ], limit=1)
                                        if not existing_tx:
                                            wallet_id.debit_wallet(
                                                amount=raw_amount,
                                                pos_order=pos_order,
                                                user_id=order_data.get('user_id'),
                                                reason=_('Sky Wallet POS Payment'),
                                            )
                                    elif raw_amount < 0:
                                        # Refund
                                        refund_amount = abs(raw_amount)
                                        existing_tx = self.env['pos.wallet.transaction'].sudo().search([
                                            ('pos_order_id', '=', pos_order.id),
                                            ('wallet_id', '=', wallet_id.id),
                                            ('payment_type', '=', 'REFUND'),
                                        ], limit=1)
                                        if not existing_tx:
                                            wallet_id.refund_wallet(
                                                amount=refund_amount,
                                                pos_order=pos_order,
                                                user_id=order_data.get('user_id'),
                                                reason=_('Sky Wallet POS Refund'),
                                            )
        return order_ids


class AccountJournal(models.Model):
    _inherit = 'pos.payment.method'

    wallet_method = fields.Boolean("Use as Sky Wallet")

    def _load_pos_data_fields(self, config_id):
        data = super()._load_pos_data_fields(config_id)
        data += ["wallet_method"]
        return data

    @api.constrains('wallet_method')
    def validate_duplicacy_in_wallet_method(self):
        journal_id = self.search([('wallet_method', '=', True)])
        if len(journal_id) > 1 and self.wallet_method == True:
            raise ValidationError(
                _("A Sky Wallet payment method already exists. Only one is allowed."))


class PosConfig(models.Model):
    _inherit = "pos.config"

    show_wallet_type = fields.Selection(
        [('checkbox', 'Sky Wallet switch'), ('payment_method', 'Sky Wallet payment method')],
        string="Sky Wallet display",
        default="checkbox",
        required=True,
    )


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    pos_show_wallet_type = fields.Selection(
        related='pos_config_id.show_wallet_type',
        readonly=False,
    )


class PosSession(models.Model):
    _inherit = 'pos.session'

    @api.model
    def _load_pos_data_models(self, config_id):
        data = super()._load_pos_data_models(config_id)
        data += ['pos.wallet', 'pos.wallet.transaction']
        return data


class ProductProduct(models.Model):
    _inherit = 'product.product'

    def _load_pos_data(self, data):
        res = super()._load_pos_data(data)
        config_id = self.env['pos.config'].browse(data['pos.config']['data'][0]['id'])
        discount_product_id = self.search([('default_code', '=', 'wk_wallet')], limit=1)
        if discount_product_id:
            product_ids_set = {product['id'] for product in res['data']}
            if discount_product_id.id not in product_ids_set:
                productModel = self.env['product.product'].with_context({**self.env.context, 'display_default_code': False})
                product = productModel.search_read([('id', '=', discount_product_id.id)], fields=res['fields'], load=False)
                self._process_pos_ui_product_product(product, config_id)
                res['data'].extend(product)
        return res
