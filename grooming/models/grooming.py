# -*- coding: utf-8 -*-
"""
Pet Grooming Models
Refactored to support Species -> Package -> Size/Age pricing and extra charges.
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class GroomingService(models.Model):
    """Grooming Service / Package Definition"""
    _name = 'grooming.service'
    _description = 'Grooming Service/Package'
    _order = 'sequence, name'
    
    name = fields.Char(string='Service/Package Name', required=True)
    description = fields.Text(string='Description', help='Details of what is included')
    sequence = fields.Integer(default=10)
    
    # Type of service
    is_addon = fields.Boolean(string='Is Add-on Treatment', default=False)
    
    # Pricing Matrix for Packages (if not addon)
    price_line_ids = fields.One2many('grooming.price', 'service_id', string='Pricing Rules')
    
    # Add-on Pricing (Fixed)
    addon_price = fields.Float(string='Add-on Price (with grooming)', default=0.0)
    addon_standalone_price = fields.Float(string='Standalone Price', default=0.0)
    
    # Link to product for billing
    product_id = fields.Many2one('product.product', string='Billing Product',
        help='Product used for invoicing this service')
    
    active = fields.Boolean(default=True)
    
    @api.model
    def create(self, vals):
        res = super(GroomingService, self).create(vals)
        if res.product_id and not res.product_id.available_in_pos:
             res.product_id.sudo().write({'available_in_pos': True})
        return res

    def write(self, vals):
        res = super(GroomingService, self).write(vals)
        if 'product_id' in vals:
            for rec in self:
                if rec.product_id and not rec.product_id.available_in_pos:
                    rec.product_id.sudo().write({'available_in_pos': True})
        return res
    
    def get_price(self, species, category, with_grooming=True):
        """Get price based on context"""
        self.ensure_one()
        if self.is_addon:
            return self.addon_price if with_grooming else self.addon_standalone_price
        
        # Find matching price rule
        rule = self.price_line_ids.filtered(
            lambda r: r.species == species and r.size_category == category
        )
        return rule[0].price if rule else 0.0


class GroomingPrice(models.Model):
    """Pricing Matrix for Grooming Packages"""
    _name = 'grooming.price'
    _description = 'Grooming Price Rule'
    _order = 'species, size_category'
    
    service_id = fields.Many2one('grooming.service', string='Package', required=True, ondelete='cascade')
    
    species = fields.Selection([
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('small_animal', 'Small Animal'),
    ], string='Species', required=True)
    
    size_category = fields.Selection([
        # Dog Sizes
        ('mini', 'Mini Breed'),
        ('small', 'Small Breed'),
        ('medium', 'Medium Breed'),
        ('large', 'Large Breed'),
        # Cat Ages
        ('kitten', 'Kitten (2-7 mo)'),
        ('adult', 'Adult Cat (7+ mo)'),
        ('senior', 'Senior Cat (5+ yr)'),
        ('hamster', 'Hamster'),
        ('junior_rabbit', 'Junior Rabbit (0-6 mo)'),
        ('adult_rabbit', 'Adult Rabbit (6+ mo)'),
        ('guinea_pig', 'Guinea Pig'),
    ], string='Size / Age Category', required=True)
    
    price = fields.Float(string='Price', required=True)


class GroomingAppointment(models.Model):
    """Grooming appointment booking"""
    _name = 'grooming.appointment'
    _description = 'Grooming Appointment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'appointment_date desc, id desc'
    
    name = fields.Char(string='Reference', compute='_compute_name', store=True)
    
    # Customer Information
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    customer_phone = fields.Char(string='Phone', related='partner_id.phone', readonly=False)
    customer_email = fields.Char(string='Email', related='partner_id.email', readonly=False)
    
    # Pet Information
    pet_id = fields.Many2one('grooming.pet', string='Pet Profile', tracking=True)
    pet_name = fields.Char(string="Pet's Name", required=True, compute='_compute_pet_info', store=True, readonly=False)
    pet_type = fields.Selection([
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('small_animal', 'Small Animal'),
        ('bird', 'Bird'),
        ('fish', 'Fish'),
        ('other', 'Other'),
    ], string='Pet Species', default='dog', required=True, compute='_compute_pet_info', store=True, readonly=False)
    
    pet_category = fields.Selection([
        # Dog Sizes
        ('mini', 'Mini Breed'),
        ('small', 'Small Breed'),
        ('medium', 'Medium Breed'),
        ('large', 'Large Breed'),
        # Cat Ages
        ('kitten', 'Kitten (2-7 mo)'),
        ('adult', 'Adult Cat (7+ mo)'),
        ('senior', 'Senior Cat (5+ yr)'),
        ('hamster', 'Hamster'),
        ('junior_rabbit', 'Junior Rabbit (0-6 mo)'),
        ('adult_rabbit', 'Adult Rabbit (6+ mo)'),
        ('guinea_pig', 'Guinea Pig'),
    ], string='Size / Age Category', required=True)
    
    # Service Selection
    service_type = fields.Selection([
        ('full_grooming', 'Full Grooming'),
        ('treatments_only', 'Treatments Only'),
    ], string='Service Type', default='full_grooming', required=True)
    
    service_id = fields.Many2one(
        'grooming.service', 
        string='Package',
        domain=[('is_addon', '=', False)]
    )
    
    addon_ids = fields.Many2many(
        'grooming.service',
        'grooming_appointment_addon_rel',
        'appointment_id',
        'service_id',
        string='Additional Treatments',
        domain=[('is_addon', '=', True)]
    )
    
    # Extra Charges & Policy
    has_detangling = fields.Boolean(string='Detangling Required')
    has_handling = fields.Boolean(string='Handling Fee Applied')
    late_pickup_hours = fields.Integer(string='Late Pickup Hours', default=0)
    
    # Scheduling
    appointment_date = fields.Datetime(string='Appointment Date & Time', required=True, tracking=True)
    preferred_time = fields.Char(string='Preferred Time Slot')
    
    # Pricing
    total_price = fields.Float(string='Total Price', compute='_compute_total', store=True)
    price_details = fields.Html(string='Price Details', compute='_compute_price_details')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id
    )
    
    # Notes
    notes = fields.Text(string='Special Requests')
    
    # Status
    state = fields.Selection([
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('checked_in', 'Checked In'),
        ('in_progress', 'Grooming In Progress'),
        ('halfway', 'Halfway Done'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', tracking=True)
    
    reminder_sent = fields.Boolean(string="Reminder Sent", default=False, copy=False)
    
    sale_order_id = fields.Many2one('sale.order', string='Sales Order', copy=False)
    pos_order_id = fields.Many2one('pos.order', string='POS Order', copy=False)
    invoice_count = fields.Integer(compute='_compute_invoice_count', string='Invoice Count')
    
    appt_payment_status = fields.Selection([
        ('paid', 'Paid'),
        ('not_paid', 'Not Paid')
    ], string='Payment Status', compute='_compute_payment_info', store=True)
    appt_payment_method = fields.Char(string='Payment Method', compute='_compute_payment_info', store=True)

    @api.depends('sale_order_id.invoice_ids.payment_state', 'pos_order_id.state', 'pos_order_id.payment_ids')
    def _compute_payment_info(self):
        for rec in self:
            status = 'not_paid'
            method = ''
            
            if rec.pos_order_id:
                if rec.pos_order_id.state in ['paid', 'done', 'invoiced']:
                    status = 'paid'
                    if rec.pos_order_id.payment_ids:
                        methods = [p.payment_method_id.name for p in rec.pos_order_id.payment_ids if p.payment_method_id]
                        method = ', '.join(set(methods))
            elif rec.sale_order_id:
                invoices = rec.sale_order_id.invoice_ids.filtered(lambda i: i.state == 'posted' and i.payment_state in ['in_payment', 'paid'])
                if invoices:
                    status = 'paid'
                    # Retrieve the payment method by traversing account.payment from invoice
                    methods = []
                    try:
                        payments = []
                        for inv in rec.sale_order_id.invoice_ids:
                            if hasattr(inv, '_get_reconciled_payments'):
                                payments.extend(inv._get_reconciled_payments())
                        if payments:
                            methods = [p.journal_id.name for p in payments if p.journal_id]
                    except Exception as e:
                        _logger.error(f"Error fetching payment method: {e}")
                    if methods:
                        method = ', '.join(set(methods))
                    else:
                        method = 'Paid via Invoice'
                        
            rec.appt_payment_status = status
            rec.appt_payment_method = method
    
    # Dynamic Policy Display
    policy_description = fields.Html(string='Policy Charges', compute='_compute_policy_description')
    
    # Audit
    create_date = fields.Datetime(string='Booked On', readonly=True)
    
    @api.depends('pet_id')
    def _compute_pet_info(self):
        for rec in self:
            if rec.pet_id:
                rec.pet_name = rec.pet_id.name
                rec.pet_type = rec.pet_id.species

    def _compute_policy_description(self):
        """Generate policy text based on current settings"""
        config = self.env['ir.config_parameter'].sudo()
        detangling = config.get_float('grooming.detangling_fee', default=100000.0)
        handling = config.get_float('grooming.handling_fee', default=20000.0)
        late_pickup = config.get_float('grooming.late_pickup_fee', default=20000.0)
        
        for rec in self:
            rec.policy_description = f"""
                <p><strong>Policy Charges:</strong></p>
                <ul>
                    <li>Detangling: +{detangling:,.0f} TZS</li>
                    <li>Handling Fee: +{handling:,.0f} TZS</li>
                    <li>Late Pickup: +{late_pickup:,.0f} TZS/hour</li>
                </ul>
            """
    
    @api.depends('pet_name', 'partner_id', 'appointment_date')
    def _compute_name(self):
        for rec in self:
            date_str = rec.appointment_date.strftime('%Y-%m-%d') if rec.appointment_date else ''
            rec.name = f"GRM-{rec.id or 'New'}: {rec.pet_name or 'Pet'} ({date_str})"
    
    @api.onchange('pet_type')
    def _onchange_pet_type(self):
        """Reset category if species changes"""
        self.pet_category = False
        
    @api.depends('service_type', 'service_id', 'addon_ids', 'pet_category', 
                 'has_detangling', 'has_handling', 'late_pickup_hours', 'pet_type')
    def _compute_price_details(self):
        """Generate detailed breakdown of costs"""
        for rec in self:
            lines = []
            
            # 1. Base Package
            if rec.service_type == 'full_grooming' and rec.service_id and rec.pet_type and rec.pet_category:
                price = rec.service_id.get_price(rec.pet_type, rec.pet_category, with_grooming=True)
                lines.append(f"<li><strong>{rec.service_id.name}</strong> ({rec.pet_category}): {price:,.0f} TZS</li>")
            
            # 2. Add-ons
            for addon in rec.addon_ids:
                price = addon.get_price(rec.pet_type, rec.pet_category, with_grooming=(rec.service_type == 'full_grooming'))
                lines.append(f"<li>{addon.name}: {price:,.0f} TZS</li>")

            # 3. Extras
            config = self.env['ir.config_parameter'].sudo()
            detangling_fee = config.get_float('grooming.detangling_fee', default=100000.0)
            handling_fee = config.get_float('grooming.handling_fee', default=20000.0)
            late_pickup_fee = config.get_float('grooming.late_pickup_fee', default=20000.0)

            if rec.has_detangling:
                lines.append(f"<li>Detangling Fee: {detangling_fee:,.0f} TZS</li>")
            
            if rec.has_handling:
                lines.append(f"<li>Handling Fee: {handling_fee:,.0f} TZS</li>")
                
            if rec.late_pickup_hours > 0:
                cost = rec.late_pickup_hours * late_pickup_fee
                lines.append(f"<li>Late Pickup ({rec.late_pickup_hours} hrs): {cost:,.0f} TZS</li>")

            if lines:
                rec.price_details = "<ul style='margin-bottom: 0; padding-left: 20px;'>" + "".join(lines) + "</ul>"
            else:
                rec.price_details = "<span class='text-muted'>No charges applied</span>"

    @api.depends('service_type', 'service_id', 'addon_ids', 'pet_category', 
                 'has_detangling', 'has_handling', 'late_pickup_hours', 'pet_type')
    def _compute_total(self):
        """Calculate total price based on matrix + extras"""
        for rec in self:
            total = 0.0
            
            # 1. Base Package Price
            if rec.service_type == 'full_grooming' and rec.service_id and rec.pet_type and rec.pet_category:
                total += rec.service_id.get_price(rec.pet_type, rec.pet_category, with_grooming=True)
            
            # 2. Add-ons
            for addon in rec.addon_ids:
                total += addon.get_price(
                    rec.pet_type, # Species doesn't affect addon fixed price usually, but passed for consistency
                    rec.pet_category,
                    with_grooming=(rec.service_type == 'full_grooming')
                )
                
            # 3. Extra Charges config
            config = self.env['ir.config_parameter'].sudo()
            detangling_fee = config.get_float('grooming.detangling_fee', default=100000.0)
            handling_fee = config.get_float('grooming.handling_fee', default=20000.0)
            late_pickup_fee = config.get_float('grooming.late_pickup_fee', default=20000.0)

            if rec.has_detangling:
                total += detangling_fee
            
            if rec.has_handling:
                total += handling_fee
                
            if rec.late_pickup_hours > 0:
                total += (rec.late_pickup_hours * late_pickup_fee)
            
            rec.total_price = total
    
    @api.constrains('appointment_date')
    def _check_appointment_date(self):
        """Validate appointment date (no Sundays)"""
        for rec in self:
            if rec.appointment_date:
                if rec.appointment_date.weekday() == 6:  # Sunday
                    raise ValidationError("We are closed on Sundays. Please choose another day.")
                if rec.appointment_date < datetime.now():
                    raise ValidationError("Appointment date cannot be in the past.")
    
    def action_confirm(self):
        """Confirm appointment, create order, and send notifications"""
        self.ensure_one()
        self.write({'state': 'confirmed'})
        
        # 1. Auto-Create Sales Order
        if not self.sale_order_id:
            self.action_create_sale_order()
            
        # Auto-Confirm Sales Order
        if self.sale_order_id and self.sale_order_id.state in ['draft', 'sent']:
            self.sale_order_id.action_confirm()
            
        # 2. Send Confirmation Email
        template = self.env.ref('grooming.email_template_grooming_confirmed', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
        
        # 3. Log Note
        self.message_post(body="Appointment confirmed. Sales Order created and confirmation email sent.")

    def action_check_in(self):
        self.ensure_one()
        self.write({'state': 'checked_in'})

    def action_start(self):
        self.write({'state': 'in_progress'})

    def action_halfway(self):
        self.ensure_one()
        self.write({'state': 'halfway'})

    def action_complete(self):
        self.write({'state': 'completed'})

    @api.model
    def _cron_check_reminders(self):
        """Send reminders for appointments scheduled for tomorrow"""
        tomorrow = datetime.now().date() + timedelta(days=1)
        start_date = datetime.combine(tomorrow, datetime.min.time())
        end_date = datetime.combine(tomorrow, datetime.max.time())
        
        appointments = self.search([
            ('state', '=', 'confirmed'),
            ('appointment_date', '>=', start_date),
            ('appointment_date', '<=', end_date),
            ('reminder_sent', '=', False),
            ('partner_id.phone', '!=', False)
        ])
        
        # WhatsApp reminders disabled as per request
        for rec in appointments:
            rec.reminder_sent = True

    def action_cancel(self):
        self.write({'state': 'cancelled'})
    
    def action_reset(self):
        self.write({'state': 'pending'})
    
    def _compute_invoice_count(self):
        """Count related invoices from sale order"""
        for rec in self:
            if rec.sale_order_id:
                rec.invoice_count = len(rec.sale_order_id.invoice_ids)
            else:
                rec.invoice_count = 0
    
    def _ensure_pos_product(self, product):
        """Ensure product is available in POS"""
        if product and not product.available_in_pos:
            product.sudo().write({'available_in_pos': True})
        return product

    def action_view_customer(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Customer',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
        }

    def action_view_pet(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pet',
            'res_model': 'grooming.pet',
            'res_id': self.pet_id.id,
            'view_mode': 'form',
        }

    def action_create_payment(self):
        """Create Invoice and Open Payment Wizard"""
        self.ensure_one()
        if not self.sale_order_id:
             # Auto-create if missing (e.g. legacy appointments or error recovery)
             self.action_create_sale_order()
             
        # Create Invoice if needed
        if not self.sale_order_id.invoice_ids:
            # Check if order is confirmed
            if self.sale_order_id.state in ['draft', 'sent']:
                self.sale_order_id.action_confirm()
            self.sale_order_id._create_invoices()

        # Post Invoices (Auto-Validate)
        invoices = self.sale_order_id.invoice_ids
        for invoice in invoices:
            if invoice.state == 'draft':
                invoice.action_post()
            
        # Open Payment Wizard
        return {
            'name': 'Pay',
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'context': {
                'active_model': 'account.move',
                'active_ids': invoices.ids,
            },
            'target': 'new',
            'type': 'ir.actions.act_window',
        }

    def action_create_sale_order(self):
        """Create a Sales Order from the grooming appointment"""
        self.ensure_one()
        if self.sale_order_id:
            raise ValidationError("A Sales Order already exists for this appointment.")
        
        SaleOrder = self.env['sale.order']
        SaleOrderLine = self.env['sale.order.line']
        
        # Create the Sales Order
        order = SaleOrder.create({
            'partner_id': self.partner_id.id,
            'origin': self.name,
            'note': f"Grooming Appointment: {self.name}",
            'pet_id': self.pet_id.id,
        })
        
        # Add main service line
        if self.service_id and self.service_id.product_id:
            product = self._ensure_pos_product(self.service_id.product_id)
            price = self.service_id.get_price(self.pet_type, self.pet_category, with_grooming=True)
            SaleOrderLine.create({
                'order_id': order.id,
                'product_id': product.id,
                'name': f"{self.service_id.name} - {self.pet_name} ({self.pet_category})",
                'product_uom_qty': 1,
                'price_unit': price,
            })
        
        # Add addon lines
        for addon in self.addon_ids:
            if addon.product_id:
                product = self._ensure_pos_product(addon.product_id)
                price = addon.get_price(self.pet_type, self.pet_category, with_grooming=(self.service_type == 'full_grooming'))
                SaleOrderLine.create({
                    'order_id': order.id,
                    'product_id': product.id,
                    'name': f"{addon.name} - {self.pet_name}",
                    'product_uom_qty': 1,
                    'price_unit': price,
                })
        
        # Add extra charges as service lines
        # Fetch products (prefer specific, fallback to misc)
        misc_product = self.env.ref('grooming.product_grooming_misc', raise_if_not_found=False)
        detangling_product = self.env.ref('grooming.product_grooming_detangling', raise_if_not_found=False) or misc_product
        handling_product = self.env.ref('grooming.product_grooming_handling', raise_if_not_found=False) or misc_product
        
        # Ensure they are POS ready
        if misc_product: self._ensure_pos_product(misc_product)
        if detangling_product: self._ensure_pos_product(detangling_product)
        if handling_product: self._ensure_pos_product(handling_product)

        config = self.env['ir.config_parameter'].sudo()
        detangling_fee = config.get_float('grooming.detangling_fee', default=100000.0)
        handling_fee = config.get_float('grooming.handling_fee', default=20000.0)
        late_pickup_fee = config.get_float('grooming.late_pickup_fee', default=20000.0)

        if self.has_detangling:
            SaleOrderLine.create({
                'order_id': order.id,
                'product_id': detangling_product.id if detangling_product else False,
                'name': f"Detangling Fee - {self.pet_name}",
                'product_uom_qty': 1,
                'price_unit': detangling_fee,
            })
        
        if self.has_handling:
            SaleOrderLine.create({
                'order_id': order.id,
                'product_id': handling_product.id if handling_product else False,
                'name': f"Handling Fee - {self.pet_name}",
                'product_uom_qty': 1,
                'price_unit': handling_fee,
            })
        
        if self.late_pickup_hours > 0:
            SaleOrderLine.create({
                'order_id': order.id,
                'product_id': misc_product.id if misc_product else False,
                'name': f"Late Pickup Fee ({self.late_pickup_hours} hrs) - {self.pet_name}",
                'product_uom_qty': 1,
                'price_unit': self.late_pickup_hours * late_pickup_fee,
            })
        
        self.sale_order_id = order.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Order',
            'res_model': 'sale.order',
            'res_id': order.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_sale_order(self):
        """Open the related Sales Order"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sales Order',
            'res_model': 'sale.order',
            'res_id': self.sale_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_invoices(self):
        """Open related invoices"""
        self.ensure_one()
        if self.sale_order_id:
            return {
                'type': 'ir.actions.act_window',
                'name': 'Invoices',
                'res_model': 'account.move',
                'domain': [('id', 'in', self.sale_order_id.invoice_ids.ids)],
                'view_mode': 'list,form',
                'views': [[False, 'list'], [False, 'form']],
                'target': 'current',
                'context': {'create': False},
            }
    
    def action_create_pos_order(self):
        """Create a POS Order from the grooming appointment"""
        self.ensure_one()
        if self.pos_order_id:
            raise ValidationError("A POS Order already exists for this appointment.")
        
        # Find an active POS session
        PosSession = self.env['pos.session']
        session = PosSession.search([('state', '=', 'opened')], limit=1)
        
        if not session:
            raise ValidationError("No active POS session found. Please open a POS session first.")
        
        PosOrder = self.env['pos.order']
        PosOrderLine = self.env['pos.order.line']
        
        # Create the POS Order (no taxes charged)
        pos_order = PosOrder.create({
            'partner_id': self.partner_id.id,
            'session_id': session.id,
            'pricelist_id': session.config_id.pricelist_id.id,
            'amount_tax': 0,
            'amount_total': 0,
            'amount_paid': 0,
            'amount_return': 0,
            'pet_id': self.pet_id.id,
        })
        
        # Add main service line
        if self.service_id and self.service_id.product_id:
            price = self.service_id.sudo().get_price(self.pet_type, self.pet_category, with_grooming=True)
            PosOrderLine.create({
                'order_id': pos_order.id,
                'product_id': self.service_id.product_id.id,
                'full_product_name': f"{self.service_id.name} - {self.pet_name}",
                'qty': 1,
                'price_unit': price,
                'price_subtotal': price,
                'price_subtotal_incl': price,
            })
        
        # Add addon lines
        for addon in self.addon_ids:
            if addon.product_id:
                price = addon.sudo().get_price(self.pet_type, self.pet_category, with_grooming=(self.service_type == 'full_grooming'))
                PosOrderLine.create({
                    'order_id': pos_order.id,
                    'product_id': addon.product_id.id,
                    'full_product_name': f"{addon.name} - {self.pet_name}",
                    'qty': 1,
                    'price_unit': price,
                    'price_subtotal': price,
                    'price_subtotal_incl': price,
                })
        
        # Add extra charges
        misc_product = self.env.ref('grooming.product_grooming_misc', raise_if_not_found=False)
        
        config = self.env['ir.config_parameter'].sudo()
        detangling_fee = config.get_float('grooming.detangling_fee', default=100000.0)
        handling_fee = config.get_float('grooming.handling_fee', default=20000.0)
        late_pickup_fee = config.get_float('grooming.late_pickup_fee', default=20000.0)
        
        if self.has_detangling and misc_product:
            PosOrderLine.create({
                'order_id': pos_order.id,
                'product_id': misc_product.id,
                'full_product_name': f"Detangling Fee - {self.pet_name}",
                'qty': 1,
                'price_unit': detangling_fee,
                'price_subtotal': detangling_fee,
                'price_subtotal_incl': detangling_fee,
            })
        
        if self.has_handling and misc_product:
            PosOrderLine.create({
                'order_id': pos_order.id,
                'product_id': misc_product.id,
                'full_product_name': f"Handling Fee - {self.pet_name}",
                'qty': 1,
                'price_unit': handling_fee,
                'price_subtotal': handling_fee,
                'price_subtotal_incl': handling_fee,
            })
        
        if self.late_pickup_hours > 0 and misc_product:
            late_fee = self.late_pickup_hours * late_pickup_fee
            PosOrderLine.create({
                'order_id': pos_order.id,
                'product_id': misc_product.id,
                'full_product_name': f"Late Pickup Fee ({self.late_pickup_hours} hrs) - {self.pet_name}",
                'qty': 1,
                'price_unit': late_fee,
                'price_subtotal': late_fee,
                'price_subtotal_incl': late_fee,
            })
        
        self.pos_order_id = pos_order.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'POS Order',
            'res_model': 'pos.order',
            'res_id': pos_order.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_view_pos_order(self):
        """Open the related POS Order"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'POS Order',
            'res_model': 'pos.order',
            'res_id': self.pos_order_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model
    def get_main_dashboard_stats(self):
        """Fetch statistics for the main dashboard"""
        uid = self.env.uid
        
        # Counts by state
        pending = self.search_count([('state', '=', 'pending')])
        confirmed = self.search_count([('state', '=', 'confirmed')])
        in_progress = self.search_count([('state', '=', 'in_progress')])
        completed = self.search_count([('state', '=', 'completed')])
        
        # Revenue (Completed appointments this month)
        start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        revenue_domain = [
            ('state', '=', 'completed'),
            ('appointment_date', '>=', start_of_month)
        ]
        revenue_recs = self.search(revenue_domain)
        total_revenue = sum(revenue_recs.mapped('total_price'))
        
        # Expenses (Posted this month)
        Expense = self.env['grooming.expense']
        expense_domain = [
            ('state', '=', 'posted'),
            ('date', '>=', start_of_month.date())
        ]
        total_expenses = sum(Expense.search(expense_domain).mapped('amount'))
        pending_expenses = Expense.search_count([('state', '=', 'draft')])
        
        # Recent Appointments (Limit 5)
        recent_appointments = self.search_read(
            [], 
            ['name', 'pet_name', 'partner_id', 'appointment_date', 'state', 'total_price'], 
            order='appointment_date desc', 
            limit=5
        )
        
        return {
            'total_appointments': pending + confirmed + in_progress + completed,
            'pending': pending,
            'confirmed': confirmed,
            'in_progress': in_progress,
            'completed': completed,
            'total_revenue_month': total_revenue,
            'total_expenses_month': total_expenses,
            'pending_expenses': pending_expenses,
            'recent_appointments': recent_appointments,
        }

