import re

with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\views\stock_picking_views.xml', 'r', encoding='utf-8') as f:
    code = f.read()

bad_xpath = '''            <xpath expr="//button[@string='Print' and @type='action']" position="attributes">
                <attribute name="invisible">picking_type_code == 'internal'</attribute>
            </xpath>'''

if bad_xpath in code:
    code = code.replace(bad_xpath, "")
    with open(r'D:\CODEX\STEPHANS OG\stephans-pet-app\grooming\views\stock_picking_views.xml', 'w', encoding='utf-8') as f:
        f.write(code)
