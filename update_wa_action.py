import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = re.sub(r'    def action_send_whatsapp\(self\):.*', '''    def action_send_whatsapp(self):
        self.ensure_one()
        return {
            'name': 'Send WhatsApp Message',
            'type': 'ir.actions.act_window',
            'res_model': 'whatsapp.transfer.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'active_id': self.id, 'active_model': 'stock.picking'}
        }''', code, flags=re.DOTALL)

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py', 'w', encoding='utf-8') as f:
    f.write(code)
