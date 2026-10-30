print("--- VERIFY START ---")
try:
    mod = env['ir.module.module'].search([('name', '=', 'custom_pos_reports')])
    print(f"MODULE STATE: {mod.state}")
except Exception as e:
    print(f"MODULE CHECK ERROR: {e}")

try:
    menu = env.ref('custom_pos_reports.menu_report_pos_weekly', raise_if_not_found=False)
    if menu:
        print(f"MENU FOUND: {menu.name} (ID: {menu.id}, Parent: {menu.parent_id.name})")
    else:
        print("MENU NOT FOUND via ref")
except Exception as e:
    print(f"MENU CHECK ERROR: {e}")

try:
    action = env.ref('custom_pos_reports.action_report_pos_weekly', raise_if_not_found=False)
    if action:
         print(f"ACTION FOUND: {action.name}")
         print(f"CONTEXT: {action.context}")
    else:
         print("ACTION NOT FOUND")

except Exception as e:
    print(f"ACTION CHECK ERROR: {e}")

print("--- VERIFY END ---")
