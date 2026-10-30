print("--- START CHECK ---")
try:
    print("CHECK_MENU:", env.ref("point_of_sale.menu_point_of_sale_report", raise_if_not_found=False))
except:
    print("CHECK_MENU: Error")

try:
    print("CHECK_VIEW:", env.ref("point_of_sale.view_pos_details_wizard", raise_if_not_found=False))
except:
    print("CHECK_VIEW: Error")

try:
    print("CHECK_ACTION:", env.ref("point_of_sale.action_report_pos_details", raise_if_not_found=False))
except:
    print("CHECK_ACTION: Error")

print("\n--- REPORTING MENUS ---")
menus = env['ir.ui.menu'].search([('name', 'ilike', 'Reporting')])
for m in menus:
    print(f"ID: {m.id} Name: {m.name} Parent: {m.parent_id.name if m.parent_id else 'None'} XMLID: {m.get_external_id()}")

print("--- END CHECK ---")
