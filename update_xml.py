import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\views\pos_details_views.xml', 'r', encoding='utf-8') as f:
    xml_code = f.read()

old_footer = '''            <xpath expr="//footer" position="inside">
                 <button name="action_export_excel" string="Export Excel" type="object" class="btn-success" invisible="not is_weekly_report"/>
                 <button name="action_print_a4" string="Export PDF (A4)" type="object" class="btn-primary" />
                 <button name="action_print_thermal" string="Thermal PDF" type="object" class="btn-secondary" invisible="not is_weekly_report"/>
            </xpath>'''

new_footer = '''            <xpath expr="//footer" position="inside">
                 <button name="action_export_excel" string="Export Excel" type="object" class="btn-success" invisible="not is_weekly_report"/>
                 <button name="action_print_a4" string="Export PDF (A4)" type="object" class="btn-primary" />
                 <button name="action_print_thermal" string="Thermal PDF" type="object" class="btn-secondary" invisible="not is_weekly_report"/>
                 <button name="action_send_whatsapp" string="Send to WhatsApp" type="object" class="btn-info text-white" icon="fa-whatsapp"/>
            </xpath>'''

if old_footer in xml_code:
    xml_code = xml_code.replace(old_footer, new_footer)
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\custom_pos_reports\views\pos_details_views.xml', 'w', encoding='utf-8') as f:
        f.write(xml_code)
    print("SUCCESS: Updated XML")
else:
    print("ERROR: Could not find footer block")
