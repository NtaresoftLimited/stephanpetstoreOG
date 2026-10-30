import re

pos_path = r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\wizard\pos_details.py'
with open(pos_path, 'r', encoding='utf-8') as f:
    pos_content = f.read()

pos_content = pos_content.replace(
'''        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
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
        }''',
'''        try:
            resp = requests.post(url, json=payload, headers=headers, timeout=15)
            resp.raise_for_status()
            res_json = resp.json()
            if not res_json.get("success"):
                raise Exception(res_json.get("message", "Unknown error from WaSender"))
        except Exception as e:
            from odoo.exceptions import UserError
            import logging
            logging.getLogger(__name__).warning("WaSender API Error: %s", str(e))
            raise UserError(f"Failed to send WhatsApp message. Error: {str(e)}")
            
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'WhatsApp Sent',
                'message': 'The Sales PDF was sent to WhatsApp!',
                'type': 'success',
                'sticky': False,
            }
        }''')

with open(pos_path, 'w', encoding='utf-8') as f:
    f.write(pos_content)
print("Updated pos_details.py locally to throw UserError.")
