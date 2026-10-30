from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PosStoreExpenseCategory(models.Model):
    _name = 'pos.store.expense.category'
    _description = 'Store Expense Category'
    _order = 'name'

    name = fields.Char(string='Category Name', required=True)
    account_id = fields.Many2one(
        'account.account',
        string='Expense Account',
        domain="[('account_type', 'in', ('expense', 'expense_direct_cost'))]",
        help="The general ledger account to debit for this category."
    )
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )

    @api.constrains('account_id', 'company_id')
    def _check_account_company(self):
        for category in self:
            if (category.account_id and category.account_id.company_ids
                    and category.company_id not in category.account_id.company_ids):
                raise ValidationError(_('The expense account is not available to this company.'))


class PosStoreExpense(models.Model):
    _name = 'pos.store.expense'
    _description = 'Store Expense'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    name = fields.Char(
        string='Expense Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    date = fields.Date(
        string='Expense Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    pos_config_id = fields.Many2one(
        'pos.config',
        string='Branch / Store',
        required=True,
        default=lambda self: self._default_pos_config_id(),
        tracking=True
    )
    category_id = fields.Many2one(
        'pos.store.expense.category',
        string='Category',
        required=True,
        tracking=True
    )
    description = fields.Char(string='Description / Purpose', required=True, tracking=True)
    amount = fields.Monetary(
        string='Amount',
        required=True,
        tracking=True,
        currency_field='currency_id'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        store=True,
        readonly=True
    )
    payment_mode = fields.Selection([
        ('cash_register', 'POS Cash Drawer (Register)'),
        ('bank_journal', 'Bank / Mobile Money')
    ], string='Paid From', default='cash_register', required=True, tracking=True)

    payment_journal_id = fields.Many2one(
        'account.journal',
        string='Payment Journal',
        domain="[('type', 'in', ('bank', 'cash'))]",
        tracking=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Recorded By',
        default=lambda self: self.env.user,
        required=True,
        readonly=True,
        tracking=True
    )
    vendor_id = fields.Many2one(
        'res.partner',
        string='Paid To / Vendor',
        tracking=True
    )
    reference = fields.Char(string='Receipt / Reference No.')
    receipt_file = fields.Binary(string='Upload Receipt', attachment=True)
    receipt_filename = fields.Char(string='Receipt Filename')

    # Workflow fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', required=True, tracking=True)

    move_id = fields.Many2one('account.move', string='Journal Entry', readonly=True, copy=False)
    reversal_move_id = fields.Many2one('account.move', string='Reversal Entry', readonly=True, copy=False)
    approved_by = fields.Many2one('res.users', string='Approved By', readonly=True, copy=False)
    approved_at = fields.Datetime(string='Approved At', readonly=True, copy=False)
    paid_by = fields.Many2one('res.users', string='Paid By', readonly=True, copy=False)
    paid_at = fields.Datetime(string='Paid At', readonly=True, copy=False)

    _sql_constraints = [
        ('expense_amount_positive', 'CHECK(amount > 0)', 'The expense amount must be greater than zero.')
    ]

    @api.model
    def _default_pos_config_id(self):
        user = self.env.user
        emp = self.env['hr.employee'].sudo().search([('user_id', '=', user.id)], limit=1)
        if emp:
            config = self.env['pos.config'].sudo().search([
                ('active', '=', True),
                '|', ('basic_employee_ids', 'in', emp.id), ('advanced_employee_ids', 'in', emp.id)
            ], limit=1)
            if config:
                return config.id
        return self.env['pos.config'].sudo().search([('active', '=', True)], limit=1).id

    @api.onchange('pos_config_id', 'payment_mode')
    def _onchange_pos_config_payment(self):
        if self.pos_config_id and self.payment_mode == 'cash_register':
            cash_method = self.pos_config_id.payment_method_ids.filtered(
                lambda m: m.journal_id and m.journal_id.type == 'cash'
            )[:1]
            if cash_method and cash_method.journal_id:
                self.payment_journal_id = cash_method.journal_id.id

    def _ensure_manager(self):
        if not self.env.su and not self.env.user.has_group('point_of_sale.group_pos_manager'):
            raise ValidationError(_('Only a Point of Sale Manager can perform this action.'))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('pos.store.expense') or _('New')
            # Auto-assign payment journal if cash register selected
            if vals.get('pos_config_id') and vals.get('payment_mode', 'cash_register') == 'cash_register' and not vals.get('payment_journal_id'):
                config = self.env['pos.config'].browse(vals['pos_config_id'])
                cash_method = config.payment_method_ids.filtered(lambda m: m.journal_id and m.journal_id.type == 'cash')[:1]
                if cash_method and cash_method.journal_id:
                    vals['payment_journal_id'] = cash_method.journal_id.id
        return super().create(vals_list)

    def write(self, vals):
        if 'state' in vals and not self.env.su and not self.env.context.get('pos_store_expense_transition'):
            raise ValidationError(_('Please use the action buttons to advance or change expense status.'))
        protected = {'category_id', 'amount', 'date', 'pos_config_id', 'payment_mode'}
        if protected.intersection(vals) and self.filtered(lambda e: e.state not in ('draft', 'submitted')) and not self.env.su:
            raise ValidationError(_('Approved or Paid expenses cannot be edited. Reset to draft or cancel first.'))
        return super().write(vals)

    def action_submit(self):
        for rec in self:
            if rec.state != 'draft':
                raise UserError(_('Only draft expenses can be submitted.'))
            rec.with_context(pos_store_expense_transition=True).write({'state': 'submitted'})

    def action_approve(self):
        for rec in self:
            rec._ensure_manager()
            if rec.state != 'submitted':
                raise UserError(_('Only submitted expenses can be approved.'))
            rec.with_context(pos_store_expense_transition=True).write({
                'state': 'approved',
                'approved_by': self.env.user.id,
                'approved_at': fields.Datetime.now(),
            })
            if rec.payment_journal_id:
                rec.action_pay()

    def action_pay(self):
        for rec in self:
            rec._ensure_manager()
            if not rec.payment_journal_id:
                raise UserError(_('Please specify a Payment Journal / Method.'))
            if not rec.category_id.account_id:
                raise UserError(_('The selected category (%s) has no expense account configured.') % rec.category_id.name)
            if not rec.payment_journal_id.default_account_id:
                raise ValidationError(_('The payment journal requires a default debit/credit account.'))

            # Create accounting move
            move_vals = {
                'journal_id': rec.payment_journal_id.id,
                'date': rec.date,
                'ref': f"{rec.name} - {rec.description}",
                'line_ids': [
                    (0, 0, {
                        'name': rec.description,
                        'account_id': rec.category_id.account_id.id,
                        'debit': rec.amount,
                        'credit': 0.0,
                        'partner_id': rec.vendor_id.id if rec.vendor_id else False,
                    }),
                    (0, 0, {
                        'name': rec.description,
                        'account_id': rec.payment_journal_id.default_account_id.id,
                        'debit': 0.0,
                        'credit': rec.amount,
                        'partner_id': rec.vendor_id.id if rec.vendor_id else False,
                    })
                ]
            }
            move = self.env['account.move'].create(move_vals)
            move.action_post()

            rec.with_context(pos_store_expense_transition=True).write({
                'move_id': move.id,
                'state': 'paid',
                'paid_by': self.env.user.id,
                'paid_at': fields.Datetime.now(),
            })

    def action_cancel(self):
        for rec in self:
            if rec.state != 'draft':
                rec._ensure_manager()
            if rec.state == 'paid' and rec.move_id and rec.move_id.state == 'posted':
                reversed_moves = rec.move_id._reverse_moves(
                    default_values_list=[{
                        'ref': _('Reversal of %s') % rec.move_id.name,
                        'date': fields.Date.context_today(rec),
                    }], cancel=True)
                rec.reversal_move_id = reversed_moves[:1]
            rec.with_context(pos_store_expense_transition=True).write({'state': 'cancelled'})

    def action_draft(self):
        for rec in self:
            rec._ensure_manager()
            rec.with_context(pos_store_expense_transition=True).write({'state': 'draft'})

    def action_view_journal_entry(self):
        self.ensure_one()
        if self.move_id:
            return {
                'name': _('Journal Entry'),
                'view_mode': 'form',
                'res_model': 'account.move',
                'res_id': self.move_id.id,
                'type': 'ir.actions.act_window',
            }
