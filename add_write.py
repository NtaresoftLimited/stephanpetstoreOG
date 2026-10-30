import os

file_path = r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\product_template.py'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

write_method = """
    def write(self, vals):
        res = super(ProductTemplate, self).write(vals)
        # Check if we should send WhatsApp (if it's still in draft and we just updated critical fields)
        if 'list_price' in vals or 'image_1920' in vals or 'categ_id' in vals:
            self._send_whatsapp_approval_if_needed()
        return res

    def _send_whatsapp_approval_if_needed(self):
        try:
            import requests
            import base64
            
            url = "https://wasenderapi.com/api/send-message"
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer 99fdd082b088ec50a4461bd03796de7e9a892770feddb7d8f0ed6e800e126856",
                "User-Agent": "Odoo/18.0"
            }
            
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            
            for record in self:
                # Ensure all required fields are met before sending
                if hasattr(record, 'approval_state') and record.approval_state == 'draft':
                    if record.list_price > 0 and record.image_1920 and record.categ_id and record.public_categ_ids:
                        product_name = record.name or 'Unknown Product'
                        product_price = record.list_price or 0.0
                        product_link = f"{base_url}/web#id={record.id}&model=product.template&view_type=form"
                        
                        message = f"🔔 *Product Updated / Needs Approval*\\n\\n"
                        message += f"📦 *Product Name:* {product_name}\\n"
                        message += f"💰 *Sales Price:* TZS {product_price:,.2f}\\n\\n"
                        message += f"It is currently blocked from sales and inventory until you review and Approve it.\\n\\n"
                        message += f"👉 *Click here to review and approve:* \\n{product_link}"
                        
                        payload = {
                            "to": "+255792079463",
                            "text": message
                        }
                        
                        if record.image_1920:
                            file_name = f"{product_name.replace(' ', '_')}.jpg"
                            attachment = self.env['ir.attachment'].sudo().create({
                                'name': file_name,
                                'type': 'binary',
                                'datas': record.image_1920,
                                'res_model': 'product.template',
                                'res_id': record.id,
                                'public': True,
                            })
                            if not attachment.access_token:
                                attachment.generate_access_token()
                                
                            doc_url = f"{base_url}/web/content/{attachment.id}/{file_name}?access_token={attachment.access_token}"
                            payload["documentUrl"] = doc_url
                            payload["fileName"] = file_name
                            
                        resp = requests.post(url, json=payload, headers=headers, timeout=10)
                        resp.raise_for_status()
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Failed to auto-send Product Approval WhatsApp: %s", str(e))
"""

if 'def write(self, vals):' not in content:
    content += write_method

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
