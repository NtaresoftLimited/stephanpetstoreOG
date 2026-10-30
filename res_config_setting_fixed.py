# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _, Command
from odoo.tools import formatLang, float_is_zero
from odoo.exceptions import AccessError, UserError, ValidationError
from collections import defaultdict
from odoo.tools import float_is_zero, float_compare
from datetime import timedelta


class BiPosSessionInherit(models.Model):
	_inherit = 'pos.session'


	def _create_invoice_receivable_lines(self, data):
		
		if self.env.user._has_group('bi_pos_paid_posted_order_delete.group_pos_delete_paid'):
			# Create invoice receivable lines for this session's move_id.
			# Keep reference of the invoice receivable lines because
			# they are reconciled with the lines in combine_inv_payment_receivable_lines
			MoveLine = data.get('MoveLine')
			combine_invoice_receivables = data.get('combine_invoice_receivables')
			split_invoice_receivables = data.get('split_invoice_receivables')

			combine_invoice_receivable_vals = defaultdict(list)
			split_invoice_receivable_vals = defaultdict(list)
			combine_invoice_receivable_lines = {}
			split_invoice_receivable_lines = {}
			for payment_method, amounts in combine_invoice_receivables.items():
				combine_invoice_receivable_vals[payment_method].append(self._get_invoice_receivable_vals(amounts['amount'], amounts['amount_converted'],payment_method))
			for payment, amounts in split_invoice_receivables.items():
				split_invoice_receivable_vals[payment].append(self._get_invoice_receivable_vals(amounts['amount'], amounts['amount_converted']))
			for payment_method, vals in combine_invoice_receivable_vals.items():
				receivable_lines = MoveLine.create(vals)
				combine_invoice_receivable_lines[payment_method] = receivable_lines
			for payment, vals in split_invoice_receivable_vals.items():
				receivable_lines = MoveLine.create(vals)
				split_invoice_receivable_lines[payment] = receivable_lines

			data.update({'combine_invoice_receivable_lines': combine_invoice_receivable_lines})
			data.update({'split_invoice_receivable_lines': split_invoice_receivable_lines})
			return data
		else:
			return super(BiPosSessionInherit, self)._create_invoice_receivable_lines(data)


	def _get_invoice_receivable_vals(self, amount, amount_converted,payment_method=None):
		if self.env.user._has_group('bi_pos_paid_posted_order_delete.group_pos_delete_paid'):
			partial_vals = {
				'account_id': self.company_id.account_default_pos_receivable_account_id.id,
				'move_id': self.move_id.id,
				'name': _('From invoice payments'),
				'delete_paid_order_string' : payment_method.name,
			}
			return self._credit_amounts(partial_vals, amount, amount_converted)
		else:
			return super(BiPosSessionInherit, self)._get_invoice_receivable_vals(amount,amount_converted)


class BiPosOrder(models.Model):
	_inherit = 'pos.order'

	def action_pos_order_cancel(self):
		if(self.env.context.get('from_custom', False)):
			return self.write({'state': 'cancel'})
		else:
			return super(BiPosOrder, self).action_pos_order_cancel()

	@api.ondelete(at_uninstall=False)
	def _unlink_except_draft_or_cancel(self):
		if self.env.user._has_group('bi_pos_paid_posted_order_delete.group_pos_delete_paid') and self.env.user.company_id.delete_paid_order:
			return
		else:
			raise ValidationError("You Can't Delete order Please contact administrator")
			super(BiPosOrder, self)._unlink_except_draft_or_cancel()



class BiAccountMoveLine_Inherit(models.Model):
	_inherit = 'account.move.line'

	delete_paid_order_string = fields.Char(string="Used for delete")


class ResConfigSettings_Inherit(models.TransientModel):
	_inherit = 'res.config.settings'

	delete_paid_order = fields.Boolean(related="company_id.delete_paid_order",readonly=False)
	set_paid_delete_order = fields.Selection(related="company_id.set_paid_delete_order",readonly=False)
	code = fields.Char(related="company_id.code",readonly=False)


class Res_company_inherit(models.Model):
	_inherit = 'res.company'

	delete_paid_order = fields.Boolean('Delete Paid Order')
	set_paid_delete_order = fields.Selection([
		('without_code', 'Delete POS Order Without Code'),
		('with_code', 'Delete POS order with Code')
		], string="POS Pricelists",default='without_code')
	code = fields.Char(string='Code')


class AccountMoveJournal(models.Model):
	_inherit = 'account.move'

	pos_order_invoice_id = fields.Many2one('pos.order', string="Pos Order.")


class PosPaymentJournal(models.Model):
	_inherit = 'pos.payment'

	def _create_payment_moves(self, is_reverse=False):
		if self.env.user._has_group('bi_pos_paid_posted_order_delete.group_pos_delete_paid'):
			result = self.env['account.move']
			for payment in self:
				order = payment.pos_order_id
				payment_method = payment.payment_method_id
				if payment_method.type == 'pay_later' or float_is_zero(payment.amount, precision_rounding=order.currency_id.rounding):
					continue
				accounting_partner = self.env["res.partner"]._find_accounting_partner(payment.partner_id)
				pos_session = order.session_id
				journal = pos_session.config_id.journal_id
				payment_move = self.env['account.move'].with_context(default_journal_id=journal.id).create({
					'journal_id': journal.id,
					'date': fields.Date.context_today(payment),
					'pos_order_invoice_id': order.id,
					'ref': _('Invoice payment for %s (%s) using %s') % (order.name, order.account_move.name, payment_method.name),
					'pos_payment_ids': payment.ids,
				})
				result |= payment_move
				payment.write({'account_move_id': payment_move.id})
				amounts = pos_session._update_amounts({'amount': 0, 'amount_converted': 0}, {'amount': payment.amount}, payment.payment_date)
				credit_line_vals = pos_session._credit_amounts({
					'account_id': accounting_partner.property_account_receivable_id.id,
					'partner_id': accounting_partner.id,
					'move_id': payment_move.id,
				}, amounts['amount'], amounts['amount_converted'])
				debit_line_vals = pos_session._debit_amounts({
					'account_id': pos_session.company_id.account_default_pos_receivable_account_id.id,
					'move_id': payment_move.id,
				}, amounts['amount'], amounts['amount_converted'])
				self.env['account.move.line'].with_context(check_move_validity=False).create([credit_line_vals, debit_line_vals])
				payment_move._post()
			return result
		else:
			return super(PosPaymentJournal, self)._create_payment_moves(is_reverse)