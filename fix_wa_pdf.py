import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\wizard\whatsapp_transfer_wizard.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_action = '''    def action_send(self):
        self.ensure_one()
        url = "https://wasenderapi.com/api/send-message"
        
        pdf_bytes = self.picking_id.generate_custom_pdf()
        pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
        
        payload = {
            "to": self.phone_number,
            "text": self.message,
            "documentBase64": pdf_b64,
            "fileName": f"Internal_Transfer_{self.picking_id.name.replace('/', '_')}.pdf"
        }'''

new_action = '''    def action_send(self):
        self.ensure_one()
        url = "https://wasenderapi.com/api/send-message"
        
        picking = self.picking_id
        pdf_bytes = picking.generate_custom_pdf()
        pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
        file_name = f"Internal_Transfer_{picking.name.replace('/', '_')}.pdf"
        
        # Store as attachment
        attachment = self.env['ir.attachment'].sudo().search([
            ('res_model', '=', 'stock.picking'),
            ('res_id', '=', picking.id),
            ('name', '=', file_name)
        ], limit=1)
        
        if attachment:
            attachment.sudo().write({'datas': pdf_b64})
        else:
            attachment = self.env['ir.attachment'].sudo().create({
                'name': file_name,
                'type': 'binary',
                'datas': pdf_b64,
                'res_model': 'stock.picking',
                'res_id': picking.id,
                'public': True,
            })
            if not attachment.access_token:
                attachment.generate_access_token()
                
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        doc_url = f"{base_url}/web/content/{attachment.id}/{file_name}?access_token={attachment.access_token}"
        
        payload = {
            "to": self.phone_number,
            "text": self.message,
            "documentUrl": doc_url,
            "fileName": file_name
        }'''

code = code.replace(old_action, new_action)

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\wizard\whatsapp_transfer_wizard.py', 'w', encoding='utf-8') as f:
    f.write(code)
