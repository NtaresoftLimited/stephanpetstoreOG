# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from datetime import datetime, date, timedelta
import logging

_logger = logging.getLogger(__name__)

class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Corporate Key-Account Identification
    is_corporate_account = fields.Boolean(
        string='Corporate Key Account',
        default=False,
        tracking=True,
        index=True,
        help="Check this to activate Corporate Key-Account CRM tracking and dynamic Q1-Q4 box logic."
    )
    corporate_tier = fields.Selection([
        ('platinum', 'Platinum VIP'),
        ('gold', 'Gold Corporate'),
        ('silver', 'Silver Corporate'),
        ('bronze', 'Bronze Partner'),
    ], string='Corporate Tier', default='silver', tracking=True)

    corporate_segment = fields.Selection([
        ('vet_clinic', 'Veterinary Clinic'),
        ('pet_hotel', 'Pet Hotel / Boarding'),
        ('breeder', 'Professional Breeder'),
        ('security_k9', 'Security / K9 Unit'),
        ('shelter_ngo', 'Animal Shelter / NGO'),
        ('retail_vip', 'High-Volume Retail VIP'),
        ('other', 'Other Corporate'),
    ], string='Corporate Segment', default='other', tracking=True)

    corporate_reg_no = fields.Char(
        string='TIN / Business Reg No.',
        help="Corporate registration number or Taxpayer Identification Number."
    )
    key_account_manager_id = fields.Many2one(
        'res.users',
        string='Key Account Manager',
        tracking=True,
        default=lambda self: self.env.user,
        help="Assigned sales manager responsible for this key account."
    )
    contract_expiry_date = fields.Date(
        string='Contract / SLA Renewal Date',
        tracking=True,
        help="Renewal date for corporate terms or SLA discount agreement."
    )

    # 4-Box Matrix (Q1, Q2, Q3, Q4)
    crm_box = fields.Selection([
        ('q1', 'Q1: Active (<30 Days)'),
        ('q2', 'Q2: Slipping (1 Month Inactive)'),
        ('q3', 'Q3: Dormant (2-3 Months Inactive)'),
        ('q4', 'Q4: Churned (>3 Months Inactive)'),
    ], string='Customer Box', default='q1', tracking=True, index=True,
       help="Dynamic quadrant classification based on purchase and grooming recency.")

    crm_box_previous = fields.Selection([
        ('q1', 'Q1: Active (<30 Days)'),
        ('q2', 'Q2: Slipping (1 Month Inactive)'),
        ('q3', 'Q3: Dormant (2-3 Months Inactive)'),
        ('q4', 'Q4: Churned (>3 Months Inactive)'),
    ], string='Previous Box', readonly=True)

    crm_box_shift_date = fields.Datetime(
        string='Last Box Shift Date',
        readonly=True,
        help="Timestamp of the most recent dynamic box promotion or demotion."
    )
    crm_box_movement = fields.Selection([
        ('promoted', 'Promoted 🔺'),
        ('demoted', 'Demoted 🔻'),
        ('stable', 'Stable ⏸️'),
    ], string='Box Movement', default='stable', readonly=True)

    crm_box_reason = fields.Char(string='Last Shift Reason', readonly=True)

    # Activity & Recency Metrics
    last_sale_date = fields.Datetime(
        string='Last Sale Date',
        compute='_compute_crm_metrics',
        store=True,
        tracking=True,
        help="Date of latest confirmed sales order or paid POS order."
    )
    last_grooming_date = fields.Datetime(
        string='Last Grooming Date',
        compute='_compute_crm_metrics',
        store=True,
        tracking=True,
        help="Date of latest completed grooming appointment."
    )
    last_activity_date = fields.Datetime(
        string='Last Activity Date',
        compute='_compute_crm_metrics',
        store=True,
        tracking=True,
        help="Latest of either sales or grooming activity."
    )
    days_since_last_sale = fields.Integer(
        string='Days Since Sale',
        compute='_compute_crm_metrics',
        store=True
    )
    days_since_last_grooming = fields.Integer(
        string='Days Since Grooming',
        compute='_compute_crm_metrics',
        store=True
    )
    days_since_last_activity = fields.Integer(
        string='Days Inactive',
        compute='_compute_crm_metrics',
        store=True,
        index=True,
        help="Days since either the last sale or the last grooming appointment."
    )

    total_spent_corporate = fields.Monetary(
        string='Total Revenue (Sales & POS)',
        compute='_compute_crm_metrics',
        store=True,
        currency_field='currency_id'
    )
    corporate_sale_orders_count = fields.Integer(
        string='Sales Orders Count',
        compute='_compute_crm_metrics',
        store=True
    )
    corporate_pos_orders_count = fields.Integer(
        string='POS Orders Count',
        compute='_compute_crm_metrics',
        store=True
    )
    corporate_grooming_count = fields.Integer(
        string='Grooming Count',
        compute='_compute_crm_metrics',
        store=True
    )
    corporate_pet_count = fields.Integer(
        string='Registered Pets',
        compute='_compute_crm_metrics',
        store=True
    )
    corporate_health_score = fields.Integer(
        string='Health Score',
        compute='_compute_crm_metrics',
        store=True,
        help="Score from 0 (Critical Churn) to 100 (Peak Loyalty) combining recency, frequency, and spend."
    )

    shift_log_ids = fields.One2many(
        'corporate.crm.shift.log',
        'partner_id',
        string='Box Shift Audit Trail'
    )
    corporate_deal_ids = fields.One2many(
        'corporate.crm.deal',
        'partner_id',
        string='Corporate Deals'
    )
    corporate_deal_count = fields.Integer(
        string='Deals Count',
        compute='_compute_corporate_deal_count'
    )

    def _compute_corporate_deal_count(self):
        for partner in self:
            partner.corporate_deal_count = len(partner.corporate_deal_ids)

    # ---------------------------------------------------------
    # COMPUTE METRICS
    # ---------------------------------------------------------
    @api.depends(
        'sale_order_ids.state', 'sale_order_ids.date_order', 'sale_order_ids.amount_total',
        'pos_order_ids.state', 'pos_order_ids.date_order', 'pos_order_ids.amount_total',
        'is_corporate_account'
    )
    def _compute_crm_metrics(self):
        now = fields.Datetime.now()
        for partner in self:
            # Gather Sales Orders (confirmed or done)
            confirmed_sales = partner.sale_order_ids.filtered(lambda s: s.state in ('sale', 'done'))
            latest_sale_so = max(confirmed_sales.mapped('date_order')) if confirmed_sales else False

            # Gather POS Orders (paid, done, invoiced)
            pos_orders = partner.pos_order_ids.filtered(lambda p: p.state in ('paid', 'done', 'invoiced'))
            latest_pos = max(pos_orders.mapped('date_order')) if pos_orders else False

            # Combine latest sale date
            sale_candidates = [d for d in [latest_sale_so, latest_pos] if d]
            latest_sale = max(sale_candidates) if sale_candidates else False

            # Gather Grooming Appointments
            # Check model exists in env
            grooming_model = self.env.get('grooming.appointment')
            if grooming_model:
                groomings = grooming_model.search([
                    ('partner_id', '=', partner.id),
                    ('state', 'in', ('confirmed', 'checked_in', 'in_progress', 'halfway', 'completed'))
                ])
                latest_grooming = max(groomings.mapped('appointment_date')) if groomings else False
                grooming_count = len(groomings)
            else:
                latest_grooming = False
                grooming_count = 0

            # Pets count
            pet_model = self.env.get('grooming.pet')
            if pet_model:
                pet_count = pet_model.search_count([('partner_id', '=', partner.id)])
            else:
                pet_count = 0

            # Latest overall activity
            activity_candidates = [d for d in [latest_sale, latest_grooming] if d]
            latest_activity = max(activity_candidates) if activity_candidates else False

            # Days since calculation
            days_sale = (now - latest_sale).days if latest_sale else 999
            days_grooming = (now - latest_grooming).days if latest_grooming else 999
            if latest_activity:
                days_act = (now - latest_activity).days
            elif partner.create_date:
                days_act = (now - partner.create_date).days
            else:
                days_act = 999

            # Monetary total
            so_total = sum(confirmed_sales.mapped('amount_total'))
            pos_total = sum(pos_orders.mapped('amount_total'))
            total_rev = so_total + pos_total

            # Health Score (0 to 100)
            # 1. Recency (max 40 pts)
            if days_act <= 14:
                recency_score = 40
            elif days_act <= 30:
                recency_score = 30
            elif days_act <= 60:
                recency_score = 15
            elif days_act <= 90:
                recency_score = 5
            else:
                recency_score = 0

            # 2. Frequency (max 30 pts)
            total_freq = len(confirmed_sales) + len(pos_orders) + grooming_count
            if total_freq >= 10:
                freq_score = 30
            elif total_freq >= 5:
                freq_score = 20
            elif total_freq >= 2:
                freq_score = 10
            elif total_freq >= 1:
                freq_score = 5
            else:
                freq_score = 0

            # 3. Spend in TZS (max 30 pts)
            if total_rev >= 5000000:
                spend_score = 30
            elif total_rev >= 2000000:
                spend_score = 20
            elif total_rev >= 500000:
                spend_score = 10
            elif total_rev > 0:
                spend_score = 5
            else:
                spend_score = 0

            partner.last_sale_date = latest_sale
            partner.last_grooming_date = latest_grooming
            partner.last_activity_date = latest_activity
            partner.days_since_last_sale = days_sale
            partner.days_since_last_grooming = days_grooming
            partner.days_since_last_activity = max(0, days_act)
            partner.total_spent_corporate = total_rev
            partner.corporate_sale_orders_count = len(confirmed_sales)
            partner.corporate_pos_orders_count = len(pos_orders)
            partner.corporate_grooming_count = grooming_count
            partner.corporate_pet_count = pet_count
            partner.corporate_health_score = min(100, recency_score + freq_score + spend_score)

    # ---------------------------------------------------------
    # DYNAMIC BOX SHIFTING ENGINE
    # ---------------------------------------------------------
    def recalculate_crm_box(self, trigger='manual', reason=None):
        """
        Calculates and dynamically shifts customer across Q1, Q2, Q3, Q4 boxes
        based on inactivity thresholds.
        """
        ir_config = self.env['ir.config_parameter'].sudo()
        q2_thresh = int(ir_config.get_param('stephans_corporate_crm.q2_days', 30))
        q3_thresh = int(ir_config.get_param('stephans_corporate_crm.q3_days', 60))
        q4_thresh = int(ir_config.get_param('stephans_corporate_crm.q4_days', 90))
        auto_activity = ir_config.get_param('stephans_corporate_crm.auto_create_activity', 'True') == 'True'

        box_order = {'q1': 1, 'q2': 2, 'q3': 3, 'q4': 4}
        box_labels = {
            'q1': 'Q1: Active (<30 Days)',
            'q2': 'Q2: Slipping (1 Month Inactive)',
            'q3': 'Q3: Dormant (2-3 Months Inactive)',
            'q4': 'Q4: Churned (>3 Months Inactive)',
        }

        for partner in self:
            partner._compute_crm_metrics()
            days = partner.days_since_last_activity

            # Determine new target box
            if days <= q2_thresh:
                target_box = 'q1'
            elif days <= q3_thresh:
                target_box = 'q2'
            elif days <= q4_thresh:
                target_box = 'q3'
            else:
                target_box = 'q4'

            old_box = partner.crm_box or 'q1'

            if target_box != old_box:
                # Movement direction
                if box_order[target_box] < box_order[old_box]:
                    movement = 'promoted'
                else:
                    movement = 'demoted'

                note_msg = reason or f"Shifted based on {days} days of inactivity (Trigger: {trigger})."

                # Create Audit Trail Log
                self.env['corporate.crm.shift.log'].create({
                    'partner_id': partner.id,
                    'from_box': old_box,
                    'to_box': target_box,
                    'movement_type': movement,
                    'trigger_source': trigger,
                    'days_inactive': days,
                    'total_spend_at_shift': partner.total_spent_corporate,
                    'notes': note_msg,
                    'user_id': self.env.user.id,
                })

                # Post Chatter message
                badge_color = {
                    'q1': '#198754',  # Success Green
                    'q2': '#ffc107',  # Warning Yellow
                    'q3': '#fd7e14',  # Danger Orange
                    'q4': '#dc3545',  # Critical Red
                }.get(target_box, '#6c757d')

                movement_icon = '🔺 Promoted' if movement == 'promoted' else '🔻 Demoted'
                chatter_body = f"""
                    <div style="border-left: 4px solid {badge_color}; padding-left: 10px; margin: 4px 0;">
                        <strong>Key-Account Dynamic Shift: {movement_icon}</strong><br/>
                        Customer shifted from <strong>{box_labels.get(old_box)}</strong> to 
                        <span style="background-color: {badge_color}; color: {'#000' if target_box == 'q2' else '#fff'}; padding: 2px 6px; border-radius: 4px; font-weight: bold;">
                            {box_labels.get(target_box)}
                        </span><br/>
                        <em>Days Inactive: {days} days | Spend: {partner.currency_id.symbol or 'TZS'} {partner.total_spent_corporate:,.0f}</em><br/>
                        <small>{note_msg}</small>
                    </div>
                """
                partner.message_post(body=chatter_body, subtype_xmlid='mail.mt_note')

                # Schedule Follow-up Activity for KAM if demoted
                if movement == 'demoted' and auto_activity:
                    kam = partner.key_account_manager_id or partner.user_id or self.env.user
                    act_summary = ""
                    act_note = ""
                    if target_box == 'q2':
                        act_summary = f"⚠️ Q2 Follow-up: {partner.name} Inactive for 1 Month"
                        act_note = (
                            f"Customer has had no sales or grooming for {days} days. "
                            f"Reach out via WhatsApp or call to schedule grooming and check replenishment supplies."
                        )
                    elif target_box == 'q3':
                        act_summary = f"🚨 Q3 Critical Win-Back: {partner.name} Dormant"
                        act_note = (
                            f"Customer has entered Q3 Dormant ({days} days inactive). High churn risk! "
                            f"Offer key-account re-activation voucher or special grooming package."
                        )
                    elif target_box == 'q4':
                        act_summary = f"🔴 Q4 Churn Review: {partner.name} Lost Account"
                        act_note = (
                            f"Account is in Q4 (>90 days inactive). Conduct churn assessment or executive outreach."
                        )

                    if act_summary:
                        act_type = self.env.ref('mail.mail_activity_data_call', raise_if_not_found=False) or \
                                   self.env.ref('mail.mail_activity_data_todo', raise_if_not_found=False)
                        if act_type:
                            self.env['mail.activity'].create({
                                'activity_type_id': act_type.id,
                                'summary': act_summary,
                                'note': act_note,
                                'res_id': partner.id,
                                'res_model_id': self.env['ir.model']._get('res.partner').id,
                                'user_id': kam.id,
                                'date_deadline': fields.Date.today() + timedelta(days=2),
                            })

                    # Also auto-create a pipeline deal in Retention stage if none open
                    if target_box in ('q2', 'q3'):
                        existing_deal = self.env['corporate.crm.deal'].search([
                            ('partner_id', '=', partner.id),
                            ('deal_type', 'in', ('q2_recovery', 'q3_recovery')),
                            ('is_won', '=', False),
                            ('is_lost', '=', False),
                        ], limit=1)
                        if not existing_deal:
                            retention_stage = self.env['corporate.crm.stage'].search([
                                ('name', 'ilike', 'Retention')
                            ], limit=1) or self.env['corporate.crm.stage'].search([], order='sequence asc', limit=1)
                            
                            deal_title = f"⚠️ Q2 Retention: {partner.name} (1 Month Inactive)" if target_box == 'q2' else f"🚨 Q3 Win-Back: {partner.name} (Dormant)"
                            deal_type = 'q2_recovery' if target_box == 'q2' else 'q3_recovery'
                            if retention_stage:
                                self.env['corporate.crm.deal'].create({
                                    'name': deal_title,
                                    'partner_id': partner.id,
                                    'deal_type': deal_type,
                                    'stage_id': retention_stage.id,
                                    'expected_revenue': (partner.total_spent_corporate * 0.25) or 500000.0,
                                    'key_account_manager_id': kam.id,
                                    'priority': '2' if target_box == 'q2' else '3',
                                    'contract_terms': f"Account slipped into {target_box.upper()} on {fields.Date.today()} with {days} days of inactivity.",
                                })

                # If promoted to Q1, mark overdue slipping activities as done
                if movement == 'promoted' and target_box == 'q1':
                    pending_activities = self.env['mail.activity'].search([
                        ('res_id', '=', partner.id),
                        ('res_model', '=', 'res.partner'),
                        ('summary', 'ilike', 'Q2 Follow-up')
                    ])
                    pending_activities.action_done()

                # Update partner state
                partner.write({
                    'crm_box_previous': old_box,
                    'crm_box': target_box,
                    'crm_box_shift_date': fields.Datetime.now(),
                    'crm_box_movement': movement,
                    'crm_box_reason': note_msg,
                })
            else:
                partner.write({
                    'crm_box_movement': 'stable'
                })

    # ---------------------------------------------------------
    # CRON RUNNER
    # ---------------------------------------------------------
    @api.model
    def _cron_shift_corporate_crm_boxes(self):
        """
        Scheduled action to evaluate all corporate accounts (or all partners
        with commercial transactions) and dynamically shift them across boxes.
        """
        _logger.info("Starting Corporate CRM dynamic box shift evaluation...")
        partners = self.search([
            '|',
            ('is_corporate_account', '=', True),
            ('crm_box', '!=', False)
        ])
        total_shifted = 0
        for partner in partners:
            old_box = partner.crm_box
            partner.recalculate_crm_box(trigger='cron', reason="Evaluated by nightly dynamic shift scheduler.")
            if partner.crm_box != old_box:
                total_shifted += 1

        _logger.info("Completed Corporate CRM box shifts: %s accounts shifted.", total_shifted)

    # ---------------------------------------------------------
    # ACTION HELPERS & BUTTONS
    # ---------------------------------------------------------
    def action_force_recalculate_box(self):
        """Button on partner form to trigger immediate box recomputation"""
        for rec in self:
            rec.recalculate_crm_box(trigger='manual', reason="Manually recalculated by user.")
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('CRM Box Recalculated'),
                'message': _('Account metrics and CRM box status have been updated successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }

    def action_view_corporate_deals(self):
        self.ensure_one()
        return {
            'name': _('Pipeline Opportunities - %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'corporate.crm.deal',
            'view_mode': 'kanban,list,form,pivot,graph',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
                'default_key_account_manager_id': self.key_account_manager_id.id or self.env.user.id
            },
        }

    def action_open_reengagement_wizard(self):
        """Opens WhatsApp & Email Re-engagement Outreach Wizard"""
        self.ensure_one()
        return {
            'name': _('Key Account Re-engagement Outreach'),
            'type': 'ir.actions.act_window',
            'res_model': 'corporate.crm.reengagement.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_crm_box': self.crm_box,
                'default_days_inactive': self.days_since_last_activity,
            }
        }

    def action_view_corporate_sales(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("sale.action_orders")
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action

    def action_view_corporate_groomings(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("grooming.action_grooming_appointment")
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action

    def action_view_corporate_pets(self):
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("grooming.action_grooming_pet")
        action['domain'] = [('partner_id', '=', self.id)]
        action['context'] = {'default_partner_id': self.id}
        return action

    def action_view_corporate_shift_logs(self):
        self.ensure_one()
        return {
            'name': _('Box Shift History - %s', self.name),
            'type': 'ir.actions.act_window',
            'res_model': 'corporate.crm.shift.log',
            'view_mode': 'list,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
