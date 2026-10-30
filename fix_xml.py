import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\views\stock_picking_views.xml', 'r', encoding='utf-8') as f:
    code = f.read()

old_xpath = '''            <xpath expr="//header" position="inside">
                <button name="action_download_custom_pdf" string="Print Transfer (Custom)" type="object" class="oe_highlight" invisible="picking_type_code != 'internal'"/>
            </xpath>'''

new_xpath = '''            <!-- Hide standard print button for internals -->
            <xpath expr="//button[@name='do_print_picking']" position="attributes">
                <attribute name="invisible">picking_type_code == 'internal'</attribute>
            </xpath>
            <xpath expr="//header" position="inside">
                <button name="action_download_custom_pdf" string="Print Internal Transfer" type="object" class="oe_highlight" invisible="picking_type_code != 'internal'"/>
                <button name="action_send_whatsapp" string="Send WhatsApp" type="object" icon="fa-whatsapp" class="btn-success oe_highlight" invisible="picking_type_code != 'internal'"/>
            </xpath>'''

code = code.replace(old_xpath, new_xpath)

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\views\stock_picking_views.xml', 'w', encoding='utf-8') as f:
    f.write(code)
