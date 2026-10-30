from odoo import Command, api, fields, models


class HrExpense(models.Model):
    _inherit = 'hr.expense'

    payment_journal_id = fields.Many2one(
        'account.journal',
        string='Payment Method',
        domain="[('type', 'in', ('bank', 'cash'))]",
        default=lambda self: self.env['account.journal'].search(
            [('type', '=', 'cash'), ('company_id', '=', self.env.company.id)],
            limit=1,
        ),
    )
    reference = fields.Char(string='Reference / Notes')
    payment_mode = fields.Selection(default='company_account')

    @api.model
    def _default_employee_id(self):
        employee = self.env.user.employee_id
        if not employee:
            employee = self.env['hr.employee'].sudo().search([('user_id', '=', self.env.uid)], limit=1)
        if not employee:
            employee = self.env['hr.employee'].sudo().search([
                '|', ('work_email', '=', self.env.user.email),
                ('name', '=ilike', self.env.user.name)
            ], limit=1)
            if employee and not employee.user_id:
                employee.sudo().write({'user_id': self.env.uid})
        if not employee and not self.env.user.has_group('hr_expense.group_hr_expense_team_approver'):
            employee = self.env['hr.employee'].sudo().create({
                'name': self.env.user.name,
                'user_id': self.env.uid,
                'work_email': self.env.user.email or False,
                'company_id': self.env.company.id,
            })
        return employee

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('employee_id'):
                emp = self.env['hr.employee'].sudo().search(
                    [('user_id', '=', self.env.uid)], limit=1
                )
                if not emp:
                    emp = self.env['hr.employee'].sudo().search([], limit=1)
                if emp:
                    vals['employee_id'] = emp.id
            if not vals.get('payment_mode'):
                vals['payment_mode'] = 'company_account'
            if 'total_amount_currency' in vals and not vals.get('total_amount'):
                vals['total_amount'] = vals['total_amount_currency']
            if 'total_amount_currency' in vals and not vals.get('price_unit'):
                vals['price_unit'] = vals['total_amount_currency']
        return super().create(vals_list)

    def write(self, vals):
        if 'total_amount_currency' in vals and 'total_amount' not in vals:
            vals['total_amount'] = vals['total_amount_currency']
        return super().write(vals)

    def _ensure_expense_outstanding_account(self):
        for expense in self:
            if not expense.company_id.expense_outstanding_account_id:
                out_acc = self.env['account.account'].sudo().search([
                    ('code', '=', '1034'),
                    ('company_id', '=', expense.company_id.id),
                ], limit=1)
                if not out_acc:
                    out_acc = self.env['account.account'].sudo().search([
                        ('name', 'ilike', 'Outstanding Payments'),
                        ('company_id', '=', expense.company_id.id),
                    ], limit=1)
                if out_acc:
                    expense.company_id.sudo().expense_outstanding_account_id = out_acc

    def action_submit_expense(self):
        self._ensure_expense_outstanding_account()
        for expense in self:
            if not expense.sheet_id:
                sheet_vals = {
                    'name': expense.name or f"{expense.product_id.name} - {expense.date}",
                    'employee_id': expense.employee_id.id,
                    'company_id': expense.company_id.id,
                    'expense_line_ids': [Command.set(expense.ids)],
                }
                if expense.payment_journal_id and expense.payment_journal_id.outbound_payment_method_line_ids:
                    sheet_vals['payment_method_line_id'] = expense.payment_journal_id.outbound_payment_method_line_ids[0].id
                sheet = self.env['hr.expense.sheet'].create(sheet_vals)
            else:
                sheet = expense.sheet_id
                if expense.payment_journal_id and expense.payment_journal_id.outbound_payment_method_line_ids:
                    sheet.payment_method_line_id = expense.payment_journal_id.outbound_payment_method_line_ids[0].id
            sheet.action_submit_sheet()
        return True

    def action_approve_expense(self):
        self._ensure_expense_outstanding_account()
        for expense in self:
            if not expense.sheet_id:
                expense.action_submit_expense()
            sheet = expense.sheet_id
            if expense.payment_journal_id and expense.payment_journal_id.outbound_payment_method_line_ids:
                sheet.payment_method_line_id = expense.payment_journal_id.outbound_payment_method_line_ids[0].id
            sheet.sudo().action_approve_expense_sheets()
        return True

    def action_post_expense_entries(self):
        self._ensure_expense_outstanding_account()
        for expense in self:
            if not expense.sheet_id:
                expense.action_submit_expense()
                expense.action_approve_expense()
            elif expense.sheet_id.state in ('draft', 'submit'):
                expense.action_approve_expense()
            sheet = expense.sheet_id
            if sheet:
                sheet.sudo().action_sheet_move_post()
        return True

    def action_refuse_expense(self):
        self.ensure_one()
        if not self.sheet_id:
            return False
        action = self.env['ir.actions.act_window']._for_xml_id('hr_expense.hr_expense_refuse_wizard_action')
        action['context'] = {
            'active_model': 'hr.expense.sheet',
            'active_ids': self.sheet_id.ids,
            'active_id': self.sheet_id.id,
            'default_sheet_ids': self.sheet_id.ids,
        }
        return action

    def action_reset_to_draft(self):
        for expense in self:
            sheet = expense.sheet_id
            if sheet:
                draft_moves = sheet.sudo().account_move_ids.filtered(lambda m: m.state == 'draft')
                if draft_moves:
                    draft_moves.unlink()
                other_expenses = sheet.expense_line_ids - expense
                expense.sheet_id = False
                if not other_expenses:
                    sheet.sudo().unlink()
            expense.write({'state': 'draft'})
        return True

    def action_pos_submit(self):
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
