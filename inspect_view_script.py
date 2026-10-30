print("--- FIELDS ---")
fields = env['pos.details.wizard'].fields_get()
print(list(fields.keys()))

print("\n--- VIEW ARCH ---")
view = env.ref('point_of_sale.view_pos_details_wizard')
print(view.arch)
