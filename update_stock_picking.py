import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_func_end = '''        picking = self.create({
            'picking_type_id': picking_type.id if picking_type else False,
            'location_id': src_location.id,
            'location_dest_id': dest_location.id,
            'origin': 'POS Stock Request',
            'move_ids': move_ids,
            'custom_source_warehouse_id': source_wh.id,
            'custom_destination_warehouse_id': dest_wh.id,
        })
        
        picking.action_confirm()
        return picking.id'''

new_func_end = '''        picking = self.create({
            'picking_type_id': picking_type.id if picking_type else False,
            'location_id': src_location.id,
            'location_dest_id': dest_location.id,
            'origin': 'POS Stock Request',
            'move_ids': move_ids,
            'custom_source_warehouse_id': source_wh.id,
            'custom_destination_warehouse_id': dest_wh.id,
        })
        
        picking.action_confirm()
        
        # Auto-send WhatsApp notification
        try:
            message = f"Hi Boss! The Internal Transfer {picking.name} is attached to this message.\\nPlease review for your Aproval."
            wizard = self.env['whatsapp.transfer.wizard'].create({
                'picking_id': picking.id,
                'phone_number': '+255792079463',
                'message': message,
            })
            wizard.action_send()
        except Exception as e:
            # Catch exceptions so it doesn't break the POS flow if WhatsApp fails
            import logging
            logging.getLogger(__name__).warning("Failed to auto-send WhatsApp from POS: %s", str(e))
            
        return picking.id'''

if old_func_end in code:
    code = code.replace(old_func_end, new_func_end)
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py', 'w', encoding='utf-8') as f:
        f.write(code)
    print("SUCCESS: Code updated.")
else:
    print("ERROR: old code block not found.")
