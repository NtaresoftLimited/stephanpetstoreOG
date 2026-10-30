import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_func_end = '''        request = self.env['grooming.stock.request'].sudo().create({
            'source_warehouse_id': source_wh.id,
            'destination_warehouse_id': dest_wh.id,
            'product_line_ids': lines,
            'state': 'submitted'
        })
            
        return request.id'''

new_func_end = '''        request = self.env['grooming.stock.request'].sudo().create({
            'source_warehouse_id': source_wh.id,
            'destination_warehouse_id': dest_wh.id,
            'product_line_ids': lines,
            'state': 'submitted'
        })
        
        # Auto-send WhatsApp notification
        try:
            import base64
            import requests
            
            pdf_bytes = request.generate_custom_pdf()
            pdf_b64 = base64.b64encode(pdf_bytes).decode('utf-8')
            file_name = f"Replenishment_Request_{request.name.replace('/', '_')}.pdf"
            
            attachment = self.env['ir.attachment'].sudo().create({
                'name': file_name,
                'type': 'binary',
                'datas': pdf_b64,
                'res_model': 'grooming.stock.request',
                'res_id': request.id,
                'public': True,
            })
            if not attachment.access_token:
                attachment.generate_access_token()
                
            base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
            doc_url = f"{base_url}/web/content/{attachment.id}/{file_name}?access_token={attachment.access_token}"
            
            payload = {
                "to": '+255792079463',
                "text": f"Hi Boss! A new Replenishment Request {request.name} has been submitted from the POS.\\nPlease review the attached PDF for your Aproval.",
                "documentUrl": doc_url,
                "fileName": file_name
            }
            headers = {
                "Content-Type": "application/json",
                "Authorization": "Bearer 99fdd082b088ec50a4461bd03796de7e9a892770feddb7d8f0ed6e800e126856",
                "User-Agent": "Odoo/18.0"
            }
            requests.post("https://wasenderapi.com/api/send-message", json=payload, headers=headers, timeout=30)
            
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("Failed to auto-send WhatsApp for Replenishment: %s", str(e))
            
        return request.id'''

if old_func_end in code:
    code = code.replace(old_func_end, new_func_end)
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("SUCCESS: Code updated in stock_picking.py.")
else:
    print("ERROR: old code block not found.")
