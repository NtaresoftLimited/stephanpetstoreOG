
print("--- UPGRADING custom_pos_reports ---")
module = env['ir.module.module'].search([('name', '=', 'custom_pos_reports')])
if module:
    print(f"Found module: {module.name} (State: {module.state})")
    try:
        module.button_immediate_upgrade()
        env.cr.commit()
        print("Upgrade command sent successfully.")
    except Exception as e:
        print(f"Error upgrading module: {e}")
else:
    print("Module 'custom_pos_reports' not found.")
print("--- DONE ---")
