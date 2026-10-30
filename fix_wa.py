import urllib.parse
import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(r'    def action_send_whatsapp\(self\):.*', '''    def action_send_whatsapp(self):
        self.ensure_one()
        import urllib.parse
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        msg = f"Hello! The Internal Transfer {self.name} is ready. You can print it here: {base_url}/print/transfer/{self.id}"
        encoded_msg = urllib.parse.quote(msg)
        return {
            'type': 'ir.actions.act_url',
            'url': f'https://wa.me/?text={encoded_msg}',
            'target': 'new',
        }''', code, flags=re.DOTALL)

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py', 'w', encoding='utf-8') as f:
    f.write(code)
