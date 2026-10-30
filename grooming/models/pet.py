# -*- coding: utf-8 -*-

from odoo import models, fields, api
from datetime import date

class GroomingBreed(models.Model):
    _name = 'grooming.breed'
    _description = 'Pet Breed'
    _order = 'name'

    name = fields.Char('Breed Name', required=True)
    species = fields.Selection([
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('bird', 'Bird'),
        ('fish', 'Fish'),
        ('other', 'Other'),
    ], string='Species', required=True, default='dog')

class GroomingPet(models.Model):
    _name = 'grooming.pet'
    _description = 'Pet'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'avatar.mixin']
    _order = 'name'

    name = fields.Char('Pet Name', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Owner', required=True, tracking=True)
    image_1920 = fields.Image("Image")
    
    species = fields.Selection([
        ('dog', 'Dog'),
        ('cat', 'Cat'),
        ('bird', 'Bird'),
        ('fish', 'Fish'),
        ('other', 'Other'),
    ], string='Species', required=True, default='dog', tracking=True)
    
    breed_id = fields.Many2one('grooming.breed', string='Breed', 
                              domain="[('species', '=', species)]", 
                              tracking=True)
    
    birth_date = fields.Date('Date of Birth')
    age = fields.Char(compute='_compute_age', string='Age')
    
    gender = fields.Selection([
        ('male', 'Male'),
        ('female', 'Female'),
    ], string='Gender')
    
    color = fields.Char('Color')
    weight = fields.Float('Weight (kg)')
    notes = fields.Text('Notes')
    
    # Tracking
    appointment_count = fields.Integer(compute='_compute_counts')
    invoice_count = fields.Integer(compute='_compute_counts')
    
    @api.depends('birth_date')
    def _compute_age(self):
        for rec in self:
            if rec.birth_date:
                today = fields.Date.today()
                delta = today - rec.birth_date
                years = delta.days // 365
                months = (delta.days % 365) // 30
                rec.age = f"{years}y {months}m"
            else:
                rec.age = False

    def _compute_counts(self):
        for rec in self:
            rec.appointment_count = self.env['grooming.appointment'].search_count([('pet_id', '=', rec.id)])
            rec.invoice_count = self.env['account.move'].search_count([('pet_id', '=', rec.id)])

    def action_view_appointments(self):
        return {
            'name': 'Appointments',
            'type': 'ir.actions.act_window',
            'res_model': 'grooming.appointment',
            'view_mode': 'list,form',
            'domain': [('pet_id', '=', self.id)],
            'context': {'default_pet_id': self.id, 'default_partner_id': self.partner_id.id}
        }

    def action_view_invoices(self):
        return {
            'name': 'Invoices',
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('pet_id', '=', self.id)],
            'context': {'default_pet_id': self.id, 'default_partner_id': self.partner_id.id}
        }
