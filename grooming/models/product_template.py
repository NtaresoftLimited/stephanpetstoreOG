from odoo import models, api, fields
from odoo.exceptions import ValidationError

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.constrains('list_price', 'image_1920', 'categ_id', 'type', 'is_storable')
    def _check_required_fields_for_save(self):
        if self.env.context.get('install_mode'):
            return
        for record in self:
            # Skip validation for services (like grooming services)
            if getattr(record, 'detailed_type', None) == 'service' or getattr(record, 'type', None) == 'service':
                continue
            if record.list_price <= 0.0:
                raise ValidationError("Sales Price is required and must be greater than 0.")
            if not record.image_1920:
                raise ValidationError("Product Picture is required.")
            if not record.categ_id:
                raise ValidationError("Category is required.")
                
            # Track Inventory? (Storable Product)
            # Odoo 18 uses is_storable, older uses detailed_type='product'
            if hasattr(record, 'is_storable'):
                if not record.is_storable:
                    raise ValidationError("You must enable 'Track Inventory' (Storable Product) for new products.")
            elif hasattr(record, 'detailed_type'):
                if record.detailed_type != 'product':
                    raise ValidationError("Product Type must be Storable Product (Track Inventory) for new products.")

    @api.model_create_multi
    def create(self, vals_list):
        records = super(ProductTemplate, self).create(vals_list)
        
        # After creating the products, send a WhatsApp notification
        try:
            import requests
            import base64
            
            url = "https://wasenderapi.com/api/send-message"
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer 99fdd082b088ec50a4461bd03796de7e9a892770feddb7d8f0ed6e800e126856",
                "User-Agent": "Odoo/18.0"
            }
            
            base_url = self.env['ir.config_parameter'].sudo().get_str('web.base.url')
            
            for record in records:
                if hasattr(record, 'approval_state') and record.approval_state == 'draft':
                    product_name = record.name or 'Unknown Product'
                    product_price = record.list_price or 0.0
                    product_link = f"{base_url}/web#id={record.id}&model=product.template&view_type=form"
                    
                    message = f"🔔 *New Product Needs Approval*\\n\\n"
                    message += f"📦 *Product Name:* {product_name}\\n"
                    message += f"💰 *Sales Price:* TZS {product_price:,.2f}\\n\\n"
                    message += f"It is currently blocked from sales and inventory until you review and Approve it.\\n\\n"
                    message += f"👉 *Click here to review and approve:* \\n{product_link}"
                    
                    payload = {
                        "to": "+255792079463",
                        "text": message
                    }
                    
                    # Attach product image if it exists
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
            
        return records

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
            
            base_url = self.env['ir.config_parameter'].sudo().get_str('web.base.url')
            
            for record in self:
                # Ensure all required fields are met before sending
                if hasattr(record, 'approval_state') and record.approval_state == 'draft':
                    if record.list_price > 0 and record.image_1920 and record.categ_id and record.public_categ_ids:
                        product_name = record.name or 'Unknown Product'
                        product_price = record.list_price or 0.0
                        product_link = f"{base_url}/web#id={record.id}&model=product.template&view_type=form"
                        
                        message = f"🔔 *Product Updated / Needs Approval*\n\n"
                        message += f"📦 *Product Name:* {product_name}\n"
                        message += f"💰 *Sales Price:* TZS {product_price:,.2f}\n\n"
                        message += f"It is currently blocked from sales and inventory until you review and Approve it.\n\n"
                        message += f"👉 *Click here to review and approve:* \n{product_link}"
                        
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
