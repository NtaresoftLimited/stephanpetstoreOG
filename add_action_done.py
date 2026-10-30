with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py', 'r', encoding='utf-8') as f:
    content = f.read()

action_done_code = '''
    def _action_done(self):
        res = super(StockPicking, self)._action_done()
        for picking in self:
            # Update any linked stock request to 'transferred'
            requests = self.env['grooming.stock.request'].sudo().search([('picking_id', '=', picking.id)])
            for req in requests:
                req.sudo().write({'state': 'transferred'})

            # Auto-send WhatsApp notification to Boss when internal transfer / replenishment is validated
            if picking.picking_type_code == 'internal' and (requests or (picking.origin and ('POS' in picking.origin or 'SR/' in picking.origin))):
                try:
                    src_name = picking.location_id.display_name or (picking.custom_source_warehouse_id.name if picking.custom_source_warehouse_id else "")
                    dest_name = picking.location_dest_id.display_name or (picking.custom_destination_warehouse_id.name if picking.custom_destination_warehouse_id else "")
                    origin_str = picking.origin or "Internal Transfer"
                    
                    msg = (
                        f"✅ *Transfer Completed & Validated!*\\n\\n"
                        f"Internal Transfer *{picking.name}* ({origin_str}) has been approved and validated.\\n"
                        f"📍 *From (Source):* {src_name}\\n"
                        f"🏁 *To (Destination):* {dest_name}\\n\\n"
                        f"Stock has been received and successfully updated in the inventory."
                    )
                    
                    wizard = self.env['whatsapp.transfer.wizard'].sudo().create({
                        'picking_id': picking.id,
                        'phone_number': '+255792079463',
                        'message': msg,
                    })
                    wizard.action_send()
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning("Failed to auto-send WhatsApp on transfer validation: %s", str(e))
                    
        return res
'''

if '_action_done' not in content:
    content = content + '\n' + action_done_code
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_picking.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Added _action_done to stock_picking.py")
else:
    print("_action_done already exists")
