# -*- coding: utf-8 -*-
import logging
from datetime import datetime, time, timedelta
from odoo import models, fields, api, _
import pytz

_logger = logging.getLogger(__name__)

class PosWhatsappConfig(models.Model):
    _name = 'pos.whatsapp.config'
    _description = 'POS WhatsApp Daily Report Configuration'

    name = fields.Char(default="WhatsApp POS Report Configuration", required=True)
    active = fields.Boolean(string="Enable Daily Reports", default=False)
    phone_numbers = fields.Char(string="WhatsApp Numbers (Comma separated)", help="Enter WhatsApp numbers with country code e.g., 255712345678, 255787654321")
    send_time = fields.Float(string="Send Time (24H Format)", default=22.0, help="E.g., 22.00 for 10:00 PM")
    last_sent_date = fields.Datetime(string="Last Sent Date")
    last_sent_status = fields.Char(string="Last Sent Status")

    def action_send_now(self):
        tz_name = self.env.user.tz or 'Africa/Dar_es_Salaam'
        user_tz = pytz.timezone(tz_name)
        now_tz = datetime.now(pytz.utc).astimezone(user_tz)
        for rec in self:
            rec._generate_and_send_report(now_tz)
        return True

    def _cron_send_daily_reports(self):
        configs = self.search([('active', '=', True)])
        if not configs:
            return

        tz_name = self.env.user.tz or 'Africa/Dar_es_Salaam'
        user_tz = pytz.timezone(tz_name)
        now_tz = datetime.now(pytz.utc).astimezone(user_tz)
        current_hour = now_tz.hour

        for config in configs:
            if not config.phone_numbers:
                continue
                
            config_hour = int(config.send_time)
            if current_hour != config_hour:
                continue
                
            config._generate_and_send_report(now_tz)

    def _generate_and_send_report(self, date_tz):
        wizard = self.env['pos.details.wizard'].create({
            'start_date': date_tz.replace(hour=0, minute=0, second=0).astimezone(pytz.utc).replace(tzinfo=None),
            'end_date': date_tz.replace(hour=23, minute=59, second=59).astimezone(pytz.utc).replace(tzinfo=None),
        })

        report = self.env.ref('custom_pos_reports.action_report_pos_a4')
        pdf_content, _report_type = report._render_qweb_pdf(wizard.ids)

        date_str = date_tz.strftime('%Y-%m-%d')
        filename = f"Daily_POS_Report_{date_str}.pdf"
        attachment = self.env['ir.attachment'].create({
            'name': filename,
            'type': 'binary',
            'datas': __import__('base64').b64encode(pdf_content),
            'res_model': 'pos.whatsapp.config',
            'res_id': self.id,
            'mimetype': 'application/pdf',
        })

        self.last_sent_date = fields.Datetime.now()
        self.last_sent_status = "Report Generated Successfully"
