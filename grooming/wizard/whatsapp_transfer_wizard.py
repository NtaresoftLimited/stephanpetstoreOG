from odoo import models, fields, api
from odoo.exceptions import UserError
import requests
import base64

class WhatsappTransferWizard(models.TransientModel):
    _name = 'whatsapp.transfer.wizard'
    _description = 'Send Transfer via WhatsApp'

    picking_id = fields.Many2one('stock.picking', required=True)
    phone_number = fields.Char(string='Phone Number', required=True, help="Include country code, e.g. 255786...")
    message = fields.Text(string='Message', required=True)

    @api.model
    def default_get(self, fields_list):
        res = super(WhatsappTransferWizard, self).default_get(fields_list)
        if self.env.context.get('active_id') and self.env.context.get('active_model') == 'stock.picking':
            picking = self.env['stock.picking'].browse(self.env.context.get('active_id'))
            res['picking_id'] = picking.id
            res['message'] = f"Hello! The Internal Transfer {picking.name} is attached to this message."
            res['phone_number'] = '+255792079463'
        return res

    def action_send(self):
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
                
        base_url = self.env['ir.config_parameter'].sudo().get_str('web.base.url')
        doc_url = f"{base_url}/web/content/{attachment.id}/{file_name}?access_token={attachment.access_token}"
        
        payload = {
            "to": self.phone_number,
            "text": self.message,
            "documentUrl": doc_url,
            "fileName": file_name
        }
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.env['ir.config_parameter'].sudo().get_param('stephans_whatsapp.api_key') or ''}",
            "User-Agent": "Odoo/18.0"
        }
        
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            res_json = response.json()
            if not res_json.get("success") and res_json.get("status") == "error":
                raise UserError(f"API Error: {res_json.get('message', 'Unknown error')}")
        except requests.exceptions.RequestException as e:
            raise UserError(f"Failed to connect to WaSender API: {str(e)}")
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'WhatsApp Sent',
                'message': 'Your PDF has been successfully sent via WaSender!',
                'type': 'success',
                'sticky': False,
            }
        }
