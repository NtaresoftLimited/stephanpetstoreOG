# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from urllib.parse import quote
from datetime import date, timedelta
import re

class CorporateCrmDeal(models.Model):
    _name = 'corporate.crm.deal'
    _description = 'Corporate Key-Account Pipeline Deal'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, date_deadline asc, id desc'

    name = fields.Char(string='Opportunity Title', required=True, tracking=True, index=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer / Corporate Account',
        required=True,
        tracking=True,
        index=True
    )
    email = fields.Char(string='Email', related='partner_id.email', readonly=False)
    phone = fields.Char(string='Phone / WhatsApp', related='partner_id.phone', readonly=False)
    active = fields.Boolean(default=True, index=True)

    stage_id = fields.Many2one(
        'corporate.crm.stage',
        string='Stage',
        tracking=True,
        index=True,
        default=lambda self: self._default_stage_id(),
        group_expand='_read_group_stage_ids'
    )
    is_won = fields.Boolean(related='stage_id.is_won', store=True, readonly=True)
    is_lost = fields.Boolean(related='stage_id.is_lost', store=True, readonly=True)

    # Business Case Deal Types
    deal_type = fields.Selection([
        ('new_b2b', 'New Corporate Account Acquisition'),
        ('grooming_fleet', 'Grooming Fleet / Service SLA Contract'),
        ('replenishment_sla', 'Monthly Food & Supplies Replenishment SLA'),
        ('q2_recovery', 'Q2 Slipping Win-Back (1 Month Inactive)'),
        ('q3_recovery', 'Q3 Dormant Account Recovery (2-3 Months Inactive)'),
        ('q4_churn_recovery', 'Q4 Churned Account Re-acquisition (>3 Months)'),
        ('upsell', 'Account Tier Upgrade / Expansion'),
    ], string='Deal / Opportunity Type', default='new_b2b', required=True, tracking=True)

    # Financials & Probability
    expected_revenue = fields.Monetary(string='Expected Contract Value', currency_field='currency_id', tracking=True)
    recurring_revenue_monthly = fields.Monetary(
        string='Monthly Recurring Value',
        currency_field='currency_id',
        tracking=True,
        help="Expected monthly spend from replenishment or recurring grooming visits."
    )
    probability = fields.Float(string='Probability (%)', default=10.0, tracking=True)
    date_deadline = fields.Date(string='Expected Close Date', tracking=True, default=lambda self: fields.Date.today() + timedelta(days=14))
    key_account_manager_id = fields.Many2one(
        'res.users',
        string='Key Account Manager',
        default=lambda self: self.env.user,
        tracking=True,
        index=True
    )
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Critical / VIP'),
    ], string='Priority', default='1', tracking=True)

    # Linked Corporate Account Snapshot
    corporate_tier = fields.Selection(related='partner_id.corporate_tier', readonly=False, string='Corporate Tier')
    corporate_segment = fields.Selection(related='partner_id.corporate_segment', readonly=False, string='Business Segment')
    current_box = fields.Selection(related='partner_id.crm_box', readonly=True, string='Current Box')
    days_inactive = fields.Integer(related='partner_id.days_since_last_activity', readonly=True, string='Days Inactive')

    # Business Case Specific Parameters
    pet_count = fields.Integer(string='Pet Fleet Count', default=1, help="Total number of pets or service animals included in this contract.")
    grooming_frequency = fields.Selection([
        ('weekly', 'Weekly'),
        ('biweekly', 'Every 2 Weeks'),
        ('monthly', 'Monthly (Recommended)'),
        ('quarterly', 'Quarterly'),
        ('ad_hoc', 'Ad-hoc / On-demand'),
    ], string='Grooming Frequency', default='monthly')

    replenishment_frequency = fields.Selection([
        ('weekly', 'Weekly Replenishment'),
        ('biweekly', 'Bi-weekly Replenishment'),
        ('monthly', 'Monthly Replenishment'),
        ('on_demand', 'On-Demand Orders'),
    ], string='Replenishment Frequency', default='monthly')

    preferred_branch = fields.Selection([
        ('masaki', 'Masaki Flagship Store'),
        ('mikocheni', 'Mikocheni Branch'),
        ('online_delivery', 'Direct Doorstep Delivery (Dar es Salaam)'),
    ], string='Preferred Branch / Fulfilment', default='online_delivery')

    contract_start_date = fields.Date(string='Contract Start Date', default=fields.Date.today)
    contract_end_date = fields.Date(string='Contract Renewal Date', default=lambda self: fields.Date.today() + timedelta(days=365))
    contract_terms = fields.Text(string='SLA & Pricing Terms')

    # Lost Reason Tracking
    lost_reason_id = fields.Many2one('corporate.crm.lost.reason', string='Lost Reason', tracking=True)
    lost_feedback = fields.Text(string='Lost Feedback / Churn Notes')

    # Smart Link Relationships
    sale_order_ids = fields.One2many('sale.order', 'corporate_deal_id', string='Quotations & Orders')
    sale_order_count = fields.Integer(compute='_compute_sale_order_count', string='Sales Orders')
    
    grooming_appointment_ids = fields.One2many('grooming.appointment', 'corporate_deal_id', string='Grooming Appointments')
    grooming_count = fields.Integer(compute='_compute_grooming_count', string='Groomings')

    # ---------------------------------------------------------
    # DEFAULTS & COMPUTES
    # ---------------------------------------------------------
    @api.model
    def _default_stage_id(self):
        stage = self.env['corporate.crm.stage'].search([], order='sequence asc', limit=1)
        return stage.id if stage else False

    @api.model
    def _read_group_stage_ids(self, stages, domain):
        return self.env['corporate.crm.stage'].search([], order='sequence asc')

    @api.depends('sale_order_ids')
    def _compute_sale_order_count(self):
        for deal in self:
            deal.sale_order_count = len(deal.sale_order_ids)

    @api.depends('grooming_appointment_ids')
    def _compute_grooming_count(self):
        for deal in self:
            deal.grooming_count = len(deal.grooming_appointment_ids)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            # Prepopulate pet count
            pet_model = self.env.get('grooming.pet')
            if pet_model:
                count = pet_model.search_count([('partner_id', '=', self.partner_id.id)])
                if count > 0:
                    self.pet_count = count
            # Automatically set manager if partner has KAM
            if self.partner_id.key_account_manager_id:
                self.key_account_manager_id = self.partner_id.key_account_manager_id

    # ---------------------------------------------------------
    # CRUD HOOKS
    # ---------------------------------------------------------
    @api.model_create_multi
    def create(self, vals_list):
        deals = super(CorporateCrmDeal, self).create(vals_list)
        for deal in deals:
            # If partner is not yet marked as corporate account, activate it
            if deal.partner_id and not deal.partner_id.is_corporate_account:
                deal.partner_id.sudo().write({'is_corporate_account': True})
            
            # Post chatter on partner
            deal.partner_id.message_post(
                body=f"<b>💼 New Deal Initiated:</b> {deal.name} (Type: {dict(self._fields['deal_type'].selection).get(deal.deal_type)}, Expected: {deal.currency_id.symbol or 'TZS'} {deal.expected_revenue:,.0f})",
                subtype_xmlid='mail.mt_note'
            )
        return deals

    def write(self, vals):
        # Stage movement logic
        if 'stage_id' in vals:
            target_stage = self.env['corporate.crm.stage'].browse(vals['stage_id'])
            if target_stage.is_won:
                vals['probability'] = 100.0
            elif target_stage.is_lost:
                vals['probability'] = 0.0

        res = super(CorporateCrmDeal, self).write(vals)

        for deal in self:
            if deal.stage_id.is_won:
                # Update partner contract renewal and promote to Q1
                if deal.contract_end_date:
                    deal.partner_id.sudo().write({'contract_expiry_date': deal.contract_end_date})
                deal.partner_id.recalculate_crm_box(
                    trigger='manual',
                    reason=f"Won Corporate Contract: {deal.name} ({deal.currency_id.symbol or 'TZS'} {deal.expected_revenue:,.0f})."
                )
        return res

    # ---------------------------------------------------------
    # PIPELINE ACTIONS
    # ---------------------------------------------------------
    def action_set_won(self):
        """Mark deal as Won and active contract"""
        won_stage = self.env['corporate.crm.stage'].search([('is_won', '=', True)], limit=1)
        if not won_stage:
            raise UserError(_("No 'Won' stage configured in Corporate CRM stages."))
        self.write({'stage_id': won_stage.id, 'probability': 100.0})
        self.message_post(
            body=f"🎉 <b>Deal WON!</b> Successfully closed corporate agreement for {self.currency_id.symbol or 'TZS'} {self.expected_revenue:,.0f}.",
            subtype_xmlid='mail.mt_comment'
        )
        return True

    def action_open_lost_wizard(self):
        """Open Lost Reason wizard"""
        self.ensure_one()
        return {
            'name': _('Mark Opportunity as Lost'),
            'type': 'ir.actions.act_window',
            'res_model': 'corporate.crm.lost.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_deal_id': self.id,
            }
        }

    def action_create_quotation(self):
        """Create a Sales Quotation directly linked to this deal"""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
        action['views'] = [(self.env.ref('sale.view_order_form').id, 'form')]
        action['context'] = {
            'default_partner_id': self.partner_id.id,
            'default_corporate_deal_id': self.id,
            'default_user_id': self.key_account_manager_id.id,
            'default_origin': f"Deal: {self.name}",
        }
        return action

    def action_schedule_grooming(self):
        """Schedule a Grooming Appointment linked to this deal"""
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("grooming.action_grooming_appointment")
        action['views'] = [(self.env.ref('grooming.view_grooming_appointment_form').id, 'form')]
        action['context'] = {
            'default_partner_id': self.partner_id.id,
            'default_corporate_deal_id': self.id,
            'default_customer_phone': self.phone,
            'default_notes': f"Corporate Deal SLA: {self.name}",
        }
        return action

    def action_open_whatsapp(self):
        """Generate pre-filled WhatsApp message to corporate contact"""
        self.ensure_one()
        if not self.phone:
            raise UserError(_("No phone number registered for customer %s.", self.partner_id.name))
        
        clean_phone = re.sub(r'[^0-9]', '', str(self.phone))
        if clean_phone.startswith('0') and len(clean_phone) == 10:
            clean_phone = '255' + clean_phone[1:]
        elif not clean_phone.startswith('255') and len(clean_phone) == 9:
            clean_phone = '255' + clean_phone

        # Pre-composed message based on deal type
        if self.deal_type == 'grooming_fleet':
            msg = (
                f"Hello {self.partner_id.name}! 🐾 This is {self.key_account_manager_id.name} from Stephan's Pet Store. "
                f"Regarding our grooming fleet proposal for your {self.pet_count} pets: we have arranged our salon slots and pricing package for you. "
                f"Shall we schedule the first batch of appointments this week?"
            )
        elif self.deal_type == 'replenishment_sla':
            msg = (
                f"Dear {self.partner_id.name}, this is Stephan's Pet Store Corporate Supply Team. "
                f"We are preparing your upcoming {self.replenishment_frequency} replenishment order. "
                f"Please let us know your current inventory levels so we can dispatch via {dict(self._fields['preferred_branch'].selection).get(self.preferred_branch)}."
            )
        elif self.deal_type in ('q2_recovery', 'q3_recovery'):
            msg = (
                f"Hello {self.partner_id.name}! Stephan's Pet Store Key Accounts Team here. "
                f"We miss seeing you and your pets! We have an exclusive corporate retention offer prepared for your account. "
                f"When would be a convenient time for a quick 2-minute catchup call?"
            )
        else:
            msg = (
                f"Hello {self.partner_id.name}! This is {self.key_account_manager_id.name} from Stephan's Pet Store regarding {self.name}. "
                f"We would love to finalize the agreement and activate your corporate account benefits. How can we assist today?"
            )

        whatsapp_url = f"https://wa.me/{clean_phone}?text={quote(msg)}"
        self.message_post(body=f"Sent WhatsApp message to +{clean_phone} for deal: {self.name}")
        return {
            'type': 'ir.actions.act_url',
            'url': whatsapp_url,
            'target': 'new',
        }

    def action_view_quotations(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_quotations_with_onboarding")
        action['domain'] = [('corporate_deal_id', '=', self.id)]
        action['context'] = {'default_corporate_deal_id': self.id, 'default_partner_id': self.partner_id.id}
        return action

    def action_view_groomings(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("grooming.action_grooming_appointment")
        action['domain'] = [('corporate_deal_id', '=', self.id)]
        action['context'] = {'default_corporate_deal_id': self.id, 'default_partner_id': self.partner_id.id}
        return action
