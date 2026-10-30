with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_request.py', 'r', encoding='utf-8') as f:
    content = f.read()

target = """            picking_vals = {
                'picking_type_id': picking_type.id if picking_type else False,
                'location_id': src_location.id,
                'location_dest_id': dest_location.id,
                'origin': request.name,
                'move_ids': [(0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': src_location.id,
                    'location_dest_id': dest_location.id,
                }) for line in request.product_line_ids]
            }

            picking = self.env['stock.picking'].create(picking_vals)
            request.picking_id = picking.id
            request.state = 'approved'"""

replacement = """            picking_vals = {
                'picking_type_id': picking_type.id if picking_type else False,
                'location_id': src_location.id,
                'location_dest_id': dest_location.id,
                'origin': request.name,
                'custom_source_warehouse_id': request.source_warehouse_id.id,
                'custom_destination_warehouse_id': request.destination_warehouse_id.id,
                'move_ids': [(0, 0, {
                    'name': line.product_id.name,
                    'product_id': line.product_id.id,
                    'product_uom_qty': line.quantity,
                    'product_uom': line.product_id.uom_id.id,
                    'location_id': src_location.id,
                    'location_dest_id': dest_location.id,
                }) for line in request.product_line_ids]
            }

            picking = self.env['stock.picking'].create(picking_vals)
            picking.action_confirm()
            request.picking_id = picking.id
            request.state = 'approved'"""

if target in content:
    content = content.replace(target, replacement)
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_request.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("Updated action_approve_request successfully")
else:
    print("Target not found, checking normalized...")
    norm_content = content.replace('\r\n', '\n')
    norm_target = target.replace('\r\n', '\n')
    norm_replacement = replacement.replace('\r\n', '\n')
    if norm_target in norm_content:
        norm_content = norm_content.replace(norm_target, norm_replacement)
        with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\models\stock_request.py', 'w', encoding='utf-8') as f:
            f.write(norm_content)
        print("Updated action_approve_request successfully (normalized)")
    else:
        print("Target still not found!")
