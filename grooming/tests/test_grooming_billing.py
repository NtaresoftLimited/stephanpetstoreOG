# -*- coding: utf-8 -*-
"""
Automated tests for Grooming Billing Integration
"""

from odoo.tests import TransactionCase, tagged
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


@tagged('post_install', '-at_install')
class TestGroomingBilling(TransactionCase):
    """Test grooming appointment to sales order flow"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test customer
        cls.partner = cls.env['res.partner'].create({
            'name': 'Test Pet Owner',
            'email': 'testowner@example.com',
            'phone': '+255789123456',
        })
        
        # Create a billable product for grooming
        cls.product = cls.env['product.product'].create({
            'name': 'Grooming Service',
            'type': 'service',
            'list_price': 50000.0,
        })
        
        # Create grooming service/package with product link
        cls.service = cls.env['grooming.service'].create({
            'name': 'Standard Package',
            'is_addon': False,
            'product_id': cls.product.id,
        })
        
        # Create pricing rule for the service
        cls.env['grooming.price'].create({
            'service_id': cls.service.id,
            'species': 'dog',
            'size_category': 'medium',
            'price': 60000.0,
        })
        
        # Create addon service
        cls.addon_product = cls.env['product.product'].create({
            'name': 'Nail Cutting',
            'type': 'service',
            'list_price': 15000.0,
        })
        
        cls.addon = cls.env['grooming.service'].create({
            'name': 'Nail Cut Only',
            'is_addon': True,
            'addon_price': 15000.0,
            'addon_standalone_price': 20000.0,
            'product_id': cls.addon_product.id,
        })
    
    def test_create_appointment(self):
        """Test creating a grooming appointment"""
        appointment = self.env['grooming.appointment'].create({
            'partner_id': self.partner.id,
            'pet_name': 'Buddy',
            'pet_type': 'dog',
            'pet_category': 'medium',
            'service_type': 'full_grooming',
            'service_id': self.service.id,
            'appointment_date': datetime.now() + timedelta(days=1),
            'preferred_time': '10:00 AM',
        })
        
        self.assertEqual(appointment.state, 'pending')
        self.assertEqual(appointment.total_price, 60000.0)
    
    def test_appointment_with_addon(self):
        """Test appointment with add-on services"""
        appointment = self.env['grooming.appointment'].create({
            'partner_id': self.partner.id,
            'pet_name': 'Max',
            'pet_type': 'dog',
            'pet_category': 'medium',
            'service_type': 'full_grooming',
            'service_id': self.service.id,
            'addon_ids': [(6, 0, [self.addon.id])],
            'appointment_date': datetime.now() + timedelta(days=2),
            'preferred_time': '02:00 PM',
        })
        
        # Base price 60000 + addon 15000 = 75000
        self.assertEqual(appointment.total_price, 75000.0)
    
    def test_appointment_with_extra_charges(self):
        """Test appointment with detangling and handling fees"""
        appointment = self.env['grooming.appointment'].create({
            'partner_id': self.partner.id,
            'pet_name': 'Lucky',
            'pet_type': 'dog',
            'pet_category': 'medium',
            'service_type': 'full_grooming',
            'service_id': self.service.id,
            'has_detangling': True,
            'has_handling': True,
            'late_pickup_hours': 2,
            'appointment_date': datetime.now() + timedelta(days=3),
            'preferred_time': '03:00 PM',
        })
        
        # Base 60000 + detangling 30000 + handling 20000 + late pickup (2*10000) = 130000
        self.assertEqual(appointment.total_price, 130000.0)
    
    def test_create_sale_order_from_appointment(self):
        """Test creating a sales order from confirmed appointment"""
        appointment = self.env['grooming.appointment'].create({
            'partner_id': self.partner.id,
            'pet_name': 'Rex',
            'pet_type': 'dog',
            'pet_category': 'medium',
            'service_type': 'full_grooming',
            'service_id': self.service.id,
            'addon_ids': [(6, 0, [self.addon.id])],
            'appointment_date': datetime.now() + timedelta(days=4),
            'preferred_time': '11:00 AM',
        })
        
        # Confirm the appointment
        appointment.action_confirm()
        self.assertEqual(appointment.state, 'confirmed')
        
        # Create sales order
        appointment.action_create_sale_order()
        
        # Verify sales order was created
        self.assertTrue(appointment.sale_order_id)
        self.assertEqual(appointment.sale_order_id.partner_id, self.partner)
        
        # Verify order lines
        order_lines = appointment.sale_order_id.order_line
        self.assertEqual(len(order_lines), 2)  # Service + Addon
    
    def test_cannot_create_duplicate_order(self):
        """Test that duplicate sales order cannot be created"""
        appointment = self.env['grooming.appointment'].create({
            'partner_id': self.partner.id,
            'pet_name': 'Duke',
            'pet_type': 'dog',
            'pet_category': 'medium',
            'service_type': 'full_grooming',
            'service_id': self.service.id,
            'appointment_date': datetime.now() + timedelta(days=5),
            'preferred_time': '09:00 AM',
        })
        
        appointment.action_confirm()
        appointment.action_create_sale_order()
        
        # Try to create another order - should raise error
        with self.assertRaises(ValidationError):
            appointment.action_create_sale_order()
    
    def test_appointment_workflow(self):
        """Test full appointment workflow"""
        appointment = self.env['grooming.appointment'].create({
            'partner_id': self.partner.id,
            'pet_name': 'Charlie',
            'pet_type': 'dog',
            'pet_category': 'small',
            'service_type': 'full_grooming',
            'service_id': self.service.id,
            'appointment_date': datetime.now() + timedelta(days=6),
            'preferred_time': '04:00 PM',
        })
        
        # Initial state
        self.assertEqual(appointment.state, 'pending')
        
        # Confirm
        appointment.action_confirm()
        self.assertEqual(appointment.state, 'confirmed')
        
        # Start
        appointment.action_start()
        self.assertEqual(appointment.state, 'in_progress')
        
        # Complete
        appointment.action_complete()
        self.assertEqual(appointment.state, 'completed')
    
    def test_sunday_validation(self):
        """Test that appointments cannot be scheduled on Sunday"""
        # Find next Sunday
        today = datetime.now()
        days_until_sunday = (6 - today.weekday()) % 7
        if days_until_sunday == 0:
            days_until_sunday = 7
        next_sunday = today + timedelta(days=days_until_sunday)
        
        with self.assertRaises(ValidationError):
            self.env['grooming.appointment'].create({
                'partner_id': self.partner.id,
                'pet_name': 'Sunday Pet',
                'pet_type': 'dog',
                'pet_category': 'medium',
                'service_type': 'full_grooming',
                'service_id': self.service.id,
                'appointment_date': next_sunday.replace(hour=10, minute=0),
                'preferred_time': '10:00 AM',
            })
