# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from urllib.parse import quote
import re

class CorporateCrmReengagementWizard(models.TransientModel):
    _name = 'corporate.crm.reengagement.wizard'
    _description = 'Key Account Re-engagement Wizard'

    partner_id = fields.Many2one('res.partner', string='Corporate Account', required=True)
    phone = fields.Char(string='Phone / WhatsApp', related='partner_id.phone', readonly=False)
    email = fields.Char(string='Email', related='partner_id.email', readonly=False)
    crm_box = fields.Selection(related='partner_id.crm_box', readonly=True, string='Current Box')
    days_inactive = fields.Integer(related='partner_id.days_since_last_activity', readonly=True, string='Days Inactive')
    
    template_type = fields.Selection([
        ('q2_checkin', 'Q2: 1-Month Inactivity Check-in & Grooming Reminder'),
        ('q3_winback', 'Q3: Dormant Account VIP Win-Back Offer (10% Discount)'),
        ('q4_reconnect', 'Q4: Executive Reconnect & Care Survey'),
        ('custom', 'Custom Message'),
    ], string='Campaign Template', default='q2_checkin', required=True)

    message_body = fields.Text(string='Message Content', compute='_compute_message_body', store=True, readonly=False)

    @api.depends('template_type', 'partner_id')
    def _compute_message_body(self):
        for wizard in self:
            partner = wizard.partner_id
            if not partner:
                wizard.message_body = ''
                continue

            # Fetch pets belonging to customer if any
            pet_model = self.env.get('grooming.pet')
            pets = pet_model.search([('partner_id', '=', partner.id)]) if pet_model else False
            pet_names = ", ".join(pets.mapped('name')) if pets else 'your pets'

            account_name = partner.name or 'Valued Customer'

            if wizard.template_type == 'q2_checkin':
                wizard.message_body = (
                    f"Hello {account_name}! 🐾\n\n"
                    f"We noticed it has been about a month since our last visit together at Stephan's Pet Store. "
                    f"How is {pet_names} doing? Pets generally look and feel their best with regular 4-week grooming cycles!\n\n"
                    f"We would love to reserve a priority grooming slot or assist with restocking your premium food and supplies. "
                    f"Would you like us to book an appointment for you this week?"
                )
            elif wizard.template_type == 'q3_winback':
                wizard.message_body = (
                    f"Dear {account_name}, 🌟\n\n"
                    f"You are one of our valued Corporate Key Accounts at Stephan's Pet Store, and we truly miss having you and {pet_names}! "
                    f"To welcome you back, we are delighted to offer an exclusive 10% VIP Privilege Discount on your next grooming session or order.\n\n"
                    f"Reply directly to this message or call us anytime, and our team will prepare everything for you."
                )
            elif wizard.template_type == 'q4_reconnect':
                wizard.message_body = (
                    f"Hello {account_name},\n\n"
                    f"This is Stephan's Pet Store Key Accounts Team. It has been a little while since we last connected, "
                    f"and we want to ensure your pets are receiving the highest standard of care and nourishment.\n\n"
                    f"We would love to hear your feedback or see how we can better support your pet care needs. "
                    f"How can we assist you today?"
                )
            else:
                wizard.message_body = f"Hello {account_name}, this is Stephan's Pet Store reaching out regarding your account."

    def _get_clean_phone(self):
        raw_phone = self.phone
        if not raw_phone:
            raise UserError(_("Please provide a phone or mobile number for %s before sending WhatsApp.", self.partner_id.name))
        clean_phone = re.sub(r'[^0-9]', '', str(raw_phone))
        # Add Tanzania country code 255 if leading with 0
        if clean_phone.startswith('0') and len(clean_phone) == 10:
            clean_phone = '255' + clean_phone[1:]
        elif not clean_phone.startswith('255') and len(clean_phone) == 9:
            clean_phone = '255' + clean_phone
        return clean_phone

    def action_send_whatsapp(self):
        self.ensure_one()
        clean_phone = self._get_clean_phone()
        msg_encoded = quote(self.message_body)
        whatsapp_url = f"https://wa.me/{clean_phone}?text={msg_encoded}"

        # Post note in chatter
        self.partner_id.message_post(
            body=f"""
                <strong>💬 WhatsApp Re-engagement Sent:</strong><br/>
                <em>To:</em> +{clean_phone}<br/>
                <em>Template:</em> {dict(self._fields['template_type'].selection).get(self.template_type)}<br/>
                <blockquote>{self.message_body.replace(chr(10), '<br/>')}</blockquote>
            """,
            subtype_xmlid='mail.mt_note'
        )

        return {
            'type': 'ir.actions.act_url',
            'url': whatsapp_url,
            'target': 'new',
        }

    def action_log_activity_done(self):
        """Logs manual outreach call/note and completes pending activities"""
        self.ensure_one()
        self.partner_id.message_post(
            body=f"""
                <strong>📞 Key Account Outreach Completed:</strong><br/>
                <em>Channel:</em> Phone / Direct Outreach<br/>
                <em>Template:</em> {dict(self._fields['template_type'].selection).get(self.template_type)}<br/>
                <blockquote>{self.message_body.replace(chr(10), '<br/>')}</blockquote>
            """,
            subtype_xmlid='mail.mt_comment'
        )

        # Mark activities done
        activities = self.env['mail.activity'].search([
            ('res_id', '=', self.partner_id.id),
            ('res_model', '=', 'res.partner')
        ])
        for act in activities:
            if 'Q2' in (act.summary or '') or 'Q3' in (act.summary or ''):
                act.action_done()

        return {'type': 'ir.actions.act_window_close'}
