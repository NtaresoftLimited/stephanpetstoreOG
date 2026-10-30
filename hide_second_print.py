import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\views\stock_picking_views.xml', 'r', encoding='utf-8') as f:
    code = f.read()

old_xpath = '''            <!-- Hide standard print button for internals -->
            <xpath expr="//button[@name='do_print_picking']" position="attributes">
                <attribute name="invisible">picking_type_code == 'internal'</attribute>
            </xpath>'''

new_xpath = '''            <!-- Hide standard print button for internals -->
            <xpath expr="//button[@name='do_print_picking']" position="attributes">
                <attribute name="invisible">picking_type_code == 'internal'</attribute>
            </xpath>
            <xpath expr="//button[@string='Print' and @type='action']" position="attributes">
                <attribute name="invisible">picking_type_code == 'internal'</attribute>
            </xpath>'''

if "string='Print' and @type='action'" not in code:
    code = code.replace(old_xpath, new_xpath)
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\views\stock_picking_views.xml', 'w', encoding='utf-8') as f:
        f.write(code)
