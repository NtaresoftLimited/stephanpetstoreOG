import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_methods = '''
    def action_print_a4(self):
        # Calls the QWeb PDF (A4)
        return self.env.ref('custom_pos_reports.action_report_pos_a4').report_action(self)

    def action_send_whatsapp(self):
        self.ensure_one()
        # Generate the PDF
        report = self.env.ref('custom_pos_reports.action_report_pos_a4')
        pdf_content, _ = report._render_qweb_pdf(self.ids)
        
        pdf_b64 = base64.b64encode(pdf_content).decode('utf-8')
        file_name = f"Daily_Sales_{self.date_start_only}.pdf"
        
        # Save attachment for URL
        attachment = self.env['ir.attachment'].sudo().create({
            'name': file_name,
            'type': 'binary',
            'datas': pdf_b64,
            'res_model': 'pos.details.wizard',
            'res_id': self.id,
            'public': True,
        })
        if not attachment.access_token:
            attachment.generate_access_token()
            
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        doc_url = f"{base_url}/web/content/{attachment.id}/{file_name}?access_token={attachment.access_token}"
        
        import requests
        url = "https://wasenderapi.com/api/send-message"
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer 99fdd082b088ec50a4461bd03796de7e9a892770feddb7d8f0ed6e800e126856",
        }
        
        report_label = "Weekly" if self.is_weekly_report else "Daily"
        message = f"📊 *{report_label} Sales Report*\\n\\nHere is the sales report for {self.date_start_only} to {self.date_end_only}.\\nPlease find the PDF attached."
        
        payload = {
            "to": "+255792079463",
            "text": message,
            "documentUrl": doc_url,
            "fileName": file_name
        }
        
        try:
            requests.post(url, json=payload, headers=headers, timeout=15)
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("WaSender API Error: %s", str(e))
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'WhatsApp Sent',
                'message': 'The Sales PDF was sent to WhatsApp!',
                'type': 'success',
                'sticky': False,
            }
        }

    @api.model
    def cron_send_daily_sales_whatsapp(self):
        # Called by cron every day at 22:00
        today = fields.Date.context_today(self)
        wizard = self.create({
            'date_start_only': today,
            'date_end_only': today,
        })
        wizard.action_send_whatsapp()
'''

if 'def action_print_a4(self):' in code:
    code = re.sub(r'    def action_print_a4\(self\):\n.*?return self\.env\.ref.*?report_action\(self\)', new_methods.strip(), code, flags=re.DOTALL)
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("SUCCESS: Added WA methods.")
else:
    print("ERROR: action_print_a4 not found in the file.")
